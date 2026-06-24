#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$SKILL_DIR/.env"

usage() {
  cat <<'EOF'
Usage: deepmap.sh [--env PATH] <command> [args]

Commands:
  match      --git-url URL
  list       [--limit N] [--offset N]
  scope      --owner OWNER --repo REPO [--branch BRANCH] [--commit COMMIT]
  structure  --owner OWNER --repo REPO [--branch BRANCH] [--commit COMMIT]
  search     --query QUERY [--repo OWNER/REPO ...] [--limit N] [--branch BRANCH] [--commit COMMIT]
  ask        --query QUERY --repo OWNER/REPO [--repo OWNER/REPO ...] [--mode fast|balanced|deep] [--poll-interval SEC] [--max-wait SEC]

The ask command submits the DeepMap investigation and polls internally until a
terminal result is returned. It prints only the final JSON data.
EOF
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' "$1"
}

load_env() {
  [[ -f "$ENV_FILE" ]] || true
  if [[ -f "$ENV_FILE" ]]; then
    while IFS='=' read -r key value || [[ -n "${key:-}" ]]; do
      key="${key%%#*}"
      key="$(printf '%s' "$key" | xargs)"
      [[ -z "$key" ]] && continue
      [[ "$key" == \#* ]] && continue
      value="${value:-}"
      value="$(printf '%s' "$value" | sed -e 's/^ *//' -e 's/ *$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")"
      export "$key=$value"
    done < "$ENV_FILE"
  fi

  [[ -n "${DEEPMAP_SITE_URL:-}" ]] || die "Missing DEEPMAP_SITE_URL in $ENV_FILE"
  [[ -n "${DEEPMAP_TOKEN:-}" ]] || die "Missing DEEPMAP_TOKEN in $ENV_FILE"
  DEEPMAP_SITE_URL="${DEEPMAP_SITE_URL%/}"
}

request_json() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local url="$DEEPMAP_SITE_URL$path"

  if [[ -n "$body" ]]; then
    curl -sS -X "$method" "$url" \
      -H "Authorization: Bearer $DEEPMAP_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$body"
  else
    curl -sS -X "$method" "$url" \
      -H "Authorization: Bearer $DEEPMAP_TOKEN"
  fi
}

unwrap_data() {
  python3 -c 'import json, sys
p = json.load(sys.stdin)
if p.get("ok") is False:
    error = p.get("error") or "deepmap_error"
    message = p.get("message") or ""
    print(error + ": " + message, file=sys.stderr)
    sys.exit(2)
print(json.dumps(p.get("data", p), ensure_ascii=False, indent=2))'
}

json_field() {
  local field="$1"
  python3 -c 'import json,sys; print((json.load(sys.stdin).get(sys.argv[1]) or ""))' "$field"
}

json_body_match() {
  python3 -c 'import json,sys; print(json.dumps({"git_url": sys.argv[1]}, ensure_ascii=False))' "$1"
}

json_body_search() {
  local query="$1" limit="$2" branch="$3" commit="$4"
  shift 4
  python3 - "$query" "$limit" "$branch" "$commit" "$@" <<'PY'
import json, sys
query, limit, branch, commit, *repos = sys.argv[1:]
body = {"query": query, "limit": int(limit)}
if repos:
    body["repos"] = repos
if branch:
    body["branch"] = branch
if commit:
    body["commit"] = commit
print(json.dumps(body, ensure_ascii=False))
PY
}

json_body_ask() {
  local query="$1" mode="$2" branch="$3" commit="$4"
  shift 4
  python3 - "$query" "$mode" "$branch" "$commit" "$@" <<'PY'
import json, sys
query, mode, branch, commit, *repos = sys.argv[1:]
body = {"query": query, "repos": repos, "mode": mode}
if branch:
    body["branch"] = branch
if commit:
    body["commit"] = commit
print(json.dumps(body, ensure_ascii=False))
PY
}

cmd_match() {
  local git_url=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --git-url) git_url="$2"; shift 2 ;;
      *) die "Unknown match arg: $1" ;;
    esac
  done
  [[ -n "$git_url" ]] || die "match requires --git-url"
  request_json POST /api/repos/match "$(json_body_match "$git_url")" | unwrap_data
}

cmd_list() {
  local limit=100 offset=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --limit) limit="$2"; shift 2 ;;
      --offset) offset="$2"; shift 2 ;;
      *) die "Unknown list arg: $1" ;;
    esac
  done
  request_json GET "/api/repos/list?limit=$limit&offset=$offset" | unwrap_data
}

cmd_scope_or_structure() {
  local kind="$1" owner="" repo="" branch="" commit=""
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --owner) owner="$2"; shift 2 ;;
      --repo) repo="$2"; shift 2 ;;
      --branch) branch="$2"; shift 2 ;;
      --commit) commit="$2"; shift 2 ;;
      *) die "Unknown $kind arg: $1" ;;
    esac
  done
  [[ -n "$owner" && -n "$repo" ]] || die "$kind requires --owner and --repo"
  local path="/api/repos/$owner/$repo/$kind"
  local sep="?"
  if [[ -n "$branch" ]]; then path+="${sep}branch=$branch"; sep="&"; fi
  if [[ -n "$commit" ]]; then path+="${sep}commit=$commit"; fi
  request_json GET "$path" | unwrap_data
}

cmd_search() {
  local query="" limit=5 branch="" commit=""
  local repos=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --query) query="$2"; shift 2 ;;
      --repo) repos+=("$2"); shift 2 ;;
      --limit) limit="$2"; shift 2 ;;
      --branch) branch="$2"; shift 2 ;;
      --commit) commit="$2"; shift 2 ;;
      *) die "Unknown search arg: $1" ;;
    esac
  done
  [[ -n "$query" ]] || die "search requires --query"
  request_json POST /api/repos/search "$(json_body_search "$query" "$limit" "$branch" "$commit" "${repos[@]}")" | unwrap_data
}

cmd_ask() {
  local query="" mode="balanced" branch="" commit="" poll_interval=3 max_wait=600 verbose=1
  local repos=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --query) query="$2"; shift 2 ;;
      --repo) repos+=("$2"); shift 2 ;;
      --mode) mode="$2"; shift 2 ;;
      --branch) branch="$2"; shift 2 ;;
      --commit) commit="$2"; shift 2 ;;
      --poll-interval) poll_interval="$2"; shift 2 ;;
      --max-wait) max_wait="$2"; shift 2 ;;
      --quiet) verbose=0; shift ;;
      *) die "Unknown ask arg: $1" ;;
    esac
  done
  [[ -n "$query" ]] || die "ask requires --query"
  [[ ${#repos[@]} -gt 0 ]] || die "ask requires at least one --repo"

  local body submitted data task_id started now status_raw status phase msg elapsed
  body="$(json_body_ask "$query" "$mode" "$branch" "$commit" "${repos[@]}")"
  submitted="$(request_json POST /api/repos/ask "$body")"
  data="$(printf '%s' "$submitted" | unwrap_data)"
  task_id="$(printf '%s' "$data" | json_field task_id)"
  [[ -n "$task_id" ]] || die "DeepMap ask response missing task_id"

  if (( verbose )); then
    printf '[deepmap] submitted task %s (mode=%s)\n' "$task_id" "$mode" >&2
  fi

  started="$(date +%s)"
  while true; do
    status_raw="$(request_json GET "/api/repos/ask/$task_id")"
    data="$(printf '%s' "$status_raw" | unwrap_data)"
    status="$(printf '%s' "$data" | json_field status)"
    phase="$(printf '%s' "$data" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("phase",""))')"
    msg="$(printf '%s' "$data" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("message",""))')"
    now="$(date +%s)"
    elapsed=$((now - started))

    case "$status" in
      finished|failed|cancelled|timeout)
        if (( verbose )); then
          printf '[deepmap] %s | %s: %s (elapsed: %ss)\n' "$status" "$phase" "$msg" "$elapsed" >&2
        fi
        printf '%s\n' "$data"
        return 0
        ;;
    esac

    if (( verbose )); then
      printf '[deepmap] %ss: %s | %s: %s\n' "$elapsed" "$status" "$phase" "$msg" >&2
    fi

    if (( elapsed >= max_wait )); then
      die "ask timed out while polling task $task_id"
    fi
    sleep "$poll_interval"
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) ENV_FILE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) break ;;
  esac
done

[[ $# -gt 0 ]] || { usage; exit 1; }
command="$1"
shift

load_env

case "$command" in
  match) cmd_match "$@" ;;
  list) cmd_list "$@" ;;
  scope) cmd_scope_or_structure scope "$@" ;;
  structure) cmd_scope_or_structure structure "$@" ;;
  search) cmd_search "$@" ;;
  ask) cmd_ask "$@" ;;
  *) usage; die "Unknown command: $command" ;;
esac
