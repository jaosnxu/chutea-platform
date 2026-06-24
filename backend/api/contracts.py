"""合同审核 API — DeepSeek AI"""
import requests, json, os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/contract-data")
STORAGE_FILE = os.path.join(UPLOAD_DIR, "contracts.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _load():
    if not os.path.exists(STORAGE_FILE): return []
    with open(STORAGE_FILE) as f: return json.load(f)


def _save(data):
    with open(STORAGE_FILE, "w") as f: json.dump(data, f, ensure_ascii=False, indent=2)


class AnalyzeRequest(BaseModel):
    text: str
    filename: str = ""


class ContractSave(BaseModel):
    id: str; name: str; content: str = ""; status: str = "draft"
    selections: dict = {}; notes: dict = {}
    approval_status: str = ""; approval_id: str = ""


SYSTEM_PROMPT = """Ты — эксперт по договорному праву РФ. Твой анализ основан на Гражданском кодексе РФ (редакция 2026 года).

Для каждого значимого пункта договора предоставь СТРОГО JSON:
{
  "clauses": [
    {
      "id": "номер статьи (например 6.19)",
      "title": "название статьи на русском",
      "original": "оригинальный текст из договора",
      "ai_analysis": "правовой анализ на основе ГК РФ 2026 с указанием конкретных статей",
      "optionA": "вариант А — максимальная защита интересов Сублицензиата",
      "optionB": "вариант Б — сбалансированный, справедливый",
      "optionC": "вариант В — позиция контрагента (что предложит другая сторона)",
      "risk": "high / med / low"
    }
  ]
}

Правила:
- Анализируй ТОЛЬКО пункты, имеющие пространство для переговоров
- Пропускай определения и технические детали
- Для каждого пункта дай 3 варианта (A/B/C)
- Вариант А должен быть наиболее выгодным для Сублицензиата (твоя сторона)
- Указывай конкретные статьи ГК РФ
- Верни ТОЛЬКО JSON, без пояснений, без markdown"""


@router.post("/analyze")
def analyze_contract(req: AnalyzeRequest):
    if not DEEPSEEK_API_KEY:
        return {"error": "DEEPSEEK_API_KEY not configured", "clauses": []}
    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": DEEPSEEK_MODEL, "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": req.text[:30000]}
            ], "temperature": 0.3, "max_tokens": 8000},
            timeout=120)
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        if content.startswith("```"): content = content.split("\n", 1)[1].rstrip("`").strip()
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "clauses": []}


@router.post("/save")
def save_contract(contract: ContractSave):
    all_contracts = _load()
    for i, c in enumerate(all_contracts):
        if c["id"] == contract.id:
            all_contracts[i] = contract.model_dump(); _save(all_contracts)
            return {"status": "updated"}
    all_contracts.append(contract.model_dump()); _save(all_contracts)
    return {"status": "saved"}


@router.get("/list")
def list_contracts(): return _load()
