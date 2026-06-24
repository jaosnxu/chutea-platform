"""
AI Provider 抽象层 — 支持多模型切换，避免单点依赖
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    tokens_used: int = 0


class AIProvider(ABC):
    """AI Provider 抽象基类"""

    @abstractmethod
    def analyze_contract(self, contract_text: str, language: str = "ru") -> AIResponse:
        """合同 3 方案分析"""
        ...

    @abstractmethod
    def rewrite_contract(self, contract_text: str, selections: dict) -> AIResponse:
        """按选定方案改写合同"""
        ...


class DoubaoProvider(AIProvider):
    """豆包 ARK API（默认 Provider）"""

    def __init__(self, api_key: str, model: str = "doubao-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"

    def _call(self, system_prompt: str, user_prompt: str) -> AIResponse:
        """调用豆包 API"""
        import requests

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
            },
            timeout=120,
        )
        data = resp.json()
        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.model,
            provider="doubao",
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
        )

    def analyze_contract(self, contract_text: str, language: str = "ru") -> AIResponse:
        system = """Ты — эксперт по договорному праву РФ. 
Для каждого значимого пункта договора предложи 3 варианта:
- Вариант А (полностью в пользу Сублицензиата)
- Вариант Б (справедливый, сбалансированный)
- Известная позиция контрагента
Формат вывода — структурированный Markdown."""
        return self._call(system, contract_text)

    def rewrite_contract(self, contract_text: str, selections: dict) -> AIResponse:
        system = """Ты — редактор договоров. 
Перепиши указанные пункты договора согласно выбранным вариантам.
Формат: <del>удалённый текст</del> <ins>новый текст</ins>"""
        user = f"Договор:\n{contract_text}\n\nВыбранные варианты:\n{selections}"
        return self._call(system, user)


def get_provider(provider_name: str = "doubao", api_key: Optional[str] = None) -> AIProvider:
    """Provider 工厂 — 支持切换"""
    import os

    key = api_key or os.getenv("DOUBAO_API_KEY", "")
    providers = {
        "doubao": DoubaoProvider(api_key=key),
        # 将来可加: "openai": OpenAIProvider(...), "claude": ClaudeProvider(...)
    }
    return providers.get(provider_name, DoubaoProvider(api_key=key))
