---
name: deepmap
description: |
  Use when the user asks about these DeepMap-analyzed repositories: phanhom/openinfo (macOS menu bar app Swift), phanhom/aip (multi language protocol), phanhom/Competitive-Programming (algorithm solutions).
  Also use for architecture, module responsibility, implementation flow, project purpose,
  optimization ideas, or cross-repository context involving the current repo and related repos.
---

# DeepMap Repository Context

## Core Principle

DeepMap provides repository-level background knowledge generated from analyzed Git repositories. Use it to understand architecture, module boundaries, implementation flow, project purpose, major functionality, optimization opportunities, and relationships between the current repo and other related repos.

DeepMap is not the source of truth for exact current code. For precise code facts, read local files first. If local code exists and conflicts with DeepMap, trust local code and mention that DeepMap may be stale.

## When To Use DeepMap

Use DeepMap when the user asks about:

- Project architecture, technical stack, module boundaries, or overall design.
- How a feature, workflow, or business logic is implemented at repository level.
- Why a module exists, what it is responsible for, or how it interacts with other modules.
- Cross-repo behavior where the current repo depends on, calls, embeds, or coordinates with another analyzed repo.
- A repo explicitly named by the user, such as "the auth-service repo" or "project-b".
- Missing context from a related repo that is not present in the local workspace.

Do not use DeepMap by default when:

- The user asks for an exact current code fact and the relevant local file is available.
- The user asks to fix a local runtime error, compile error, failing test, or stack trace without needing architecture context.
- The user asks to implement a straightforward local change and the needed context is already in the workspace.
- No relevant analyzed repo can be found.

## Discovery Workflow

Before querying knowledge, determine which DeepMap repo or repos are relevant.

1. Identify the current Git repository from local Git remote URL.
2. Call `POST /api/repos/match` with the current remote URL to check whether the current repo has DeepMap knowledge.
3. Call `GET /api/repos/list` to discover accessible analyzed repos when the task mentions other services, packages, or related systems.
4. Select repos by evidence: exact user mention, current repo match, dependency names, service names, import/package references, or README/docs references.
5. Call `GET /api/repos/{owner}/{repo}/scope` for selected repos when confidence matters. Prefer repos whose `index_status` is `healthy` and whose coverage is adequate.

If the user is vague, start with the current repo. If the user names another repo, query that repo directly. If a repo is merely accessible but unrelated, do not query it.

## Query Strategy

Use the lightest endpoint that can answer the question.

| Need | Preferred script command | What it does |
|------|--------------------------|--------------|
| Check whether local repo has knowledge | `scripts/deepmap.sh match --git-url <url>` | Calls `POST /api/repos/match` and anchors current repo context. |
| Discover related analyzed repos | `scripts/deepmap.sh list` | Calls `GET /api/repos/list`; use names, descriptions, status, languages, and docs count to choose candidates. |
| Check health/coverage | `scripts/deepmap.sh scope --owner <owner> --repo <repo>` | Calls `GET /api/repos/{owner}/{repo}/scope`; use before relying on important conclusions. |
| Find relevant docs quickly | `scripts/deepmap.sh search --query <q> --repo owner/repo` | Calls `POST /api/repos/search`; first choice for natural-language architecture or implementation questions. |
| Browse document layout | `scripts/deepmap.sh structure --owner <owner> --repo <repo>` | Calls `GET /api/repos/{owner}/{repo}/structure`; use when search results are broad. |
| Deep multi-step investigation | `scripts/deepmap.sh ask --query <q> --repo owner/repo` | Submits the investigation and polls internally until the final result. |

Prefer `search` before `ask`. Use `ask` when the task requires synthesis across multiple files, modules, or repos. Do not manually implement ask polling; the script hides the async protocol and prints the final JSON.

## Configuration

The helper script reads `.cursor/skills/deepmap/.env` by default:

```env
DEEPMAP_SITE_URL=http://172.31.16.12:18000/deepmap
DEEPMAP_TOKEN=replace-with-deepmap-bearer-token
```

Environment variables override the `.env` file. Never print or hard-code the token in answers.

## HTTP Contracts

Use `{DEEPMAP_SITE_URL}` as the DeepMap host and pass auth with `Authorization: Bearer {token}`.

### Match current repo

```http
POST /api/repos/match
Content-Type: application/json

{"git_url":"https://github.com/org/project.git"}
```

Use this to connect the local workspace to its DeepMap knowledge. If not matched, do not pretend DeepMap covers the current repo.

### List accessible repos

```http
GET /api/repos/list?limit=100&offset=0
```

Use this for related-repo discovery. Only select repos that are relevant to the current task.

### Search knowledge

```bash
.cursor/skills/deepmap/scripts/deepmap.sh search \
  --query "JWT token 签发和验证流程" \
  --repo tokfinity/project-x \
  --limit 5
```

Search supports multiple repos. If `repos` is omitted, DeepMap may search all accessible repos, but agents should avoid broad searches unless the user explicitly asks for broad discovery.

Search results include `repo`, `file_path`, `doc_type`, `start_line`, `end_line`, `snippet`, `score`, and `url`. Use these as citations.

### Ask investigation

```bash
.cursor/skills/deepmap/scripts/deepmap.sh ask \
  --query "分析认证模块的整体架构，包括 JWT 签发、验证、刷新的流程" \
  --repo tokfinity/project-x \
  --repo tokfinity/auth-service \
  --mode balanced
```

The script handles the HTTP submit-and-poll cycle internally. Use `fast` for simple questions, `balanced` by default, and `deep` for cross-module or cross-repo investigations.

## Multi-Repo Rules

- If the current local repo is associated with multiple DeepMap repos and the user asks a vague question, prioritize the current repo.
- If the user explicitly names repo B, query repo B directly even if the local workspace is repo A.
- If repo A depends on repo B and local source for B is absent, use DeepMap for B to understand the external behavior.
- If repo A is associated with repo C but the task has no relation to C, do not query C.
- For cross-repo questions, search each relevant repo or submit one `ask` task with all relevant `repos`.

## Evidence Rules

When answering with DeepMap:

- Cite repo and generated document path when available.
- Include line ranges or URLs from `search`/`ask` citations when available.
- State uncertainty when `scope.index_status` is not healthy, coverage is low, or search returned keyword fallback.
- For exact implementation claims, verify local source if the file exists in the current workspace.
- If local code and DeepMap disagree, say so and prefer local code.

## Version Rules

Knowledge endpoints accept optional `branch` and `commit`.

- No `branch` or `commit`: use the latest generated commit on the repo HEAD branch.
- Only `branch`: use the latest generated commit on that branch.
- Only `commit`: use that commit snapshot.
- Both: exact match for that branch and commit.

Use explicit `branch`/`commit` when the user asks about a specific version, release, or historical behavior. Otherwise use defaults.

## Error Handling

| Error | Meaning | Agent behavior |
|-------|---------|----------------|
| `unauthorized` | Auth token missing/expired | Ask for valid DeepMap auth; do not retry blindly. |
| `forbidden` | User lacks permission | Explain permission issue; do not claim repo is absent. |
| `repo_not_found` | Repo absent or inaccessible | Try `/list` for accessible repos; ask user to confirm repo if needed. |
| `knowledge_not_ready` | Knowledge not generated | Do not use DeepMap for that repo; fall back to local/source docs. |
| `doc_not_found` | Generated doc path absent | Re-run `structure` or `search` to find valid paths. |
| `task_limit_exceeded` | Too many ask tasks | Wait or use `search`/`doc` instead. |
| `server_error` | DeepMap service problem | Fall back to local analysis and mention DeepMap was unavailable. |

## Common Mistakes

- Querying every accessible repo just because `/list` returns it. Select repos by relevance.
- Using DeepMap to answer exact current-code questions without checking local files.
- Treating generated knowledge as live. It may lag behind local branch or commit.
- Calling `ask` for simple lookup questions that `search` can answer faster.
- Ignoring citations. DeepMap answers should be grounded in repo/path/line evidence.
- Assuming no match means no relationship. It may mean no permission, stale auth, or a repo URL mismatch.
