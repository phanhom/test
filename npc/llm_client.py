"""LLM 客户端 - 对接大模型 API (OpenAI 兼容)"""

import json
import urllib.request
import urllib.error
from typing import Optional


class LLMClient:
    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, system_prompt: str, user_message: str) -> Optional[str]:
        """发送对话并返回回复"""
        if not self.api_key:
            return "请先在 config.json 中配置 api_key。"

        url = f"{self.base_url}/chat/completions"
        data = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 150,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip() if content else "（无回复）"
        except urllib.error.HTTPError as e:
            return f"API 错误: {e.code}"
        except urllib.error.URLError as e:
            return f"网络错误: {e.reason}"
        except Exception as e:
            return f"错误: {str(e)}"
