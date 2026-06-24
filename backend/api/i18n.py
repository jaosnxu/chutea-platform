"""
多语言 API — 后台可配置
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/i18n", tags=["i18n"])

# 默认中文 + 俄文配置
DEFAULT_I18N = {
    "zh": {
        "upload": "上传合同",
        "analyze": "AI 分析中...",
        "option_a": "方案 A（利己）",
        "option_b": "方案 B（公平）",
        "opponent": "已知对方立场",
        "supplement": "你的补充",
        "approve": "通过",
        "reject": "驳回",
        "reject_reason": "驳回理由",
        "send_approval": "发送审批",
        "audit_amounts": "金额检查",
        "audit_formulas": "公式检查",
        "audit_text": "文字检查",
        "audit_layout": "排版检查",
        "audit_risk": "风险评估",
        "audit_consistency": "一致性检查",
    },
    "ru": {
        "upload": "Загрузить договор",
        "analyze": "AI анализ...",
        "option_a": "Вариант А (в пользу Сублицензиата)",
        "option_b": "Вариант Б (справедливый)",
        "opponent": "Позиция контрагента",
        "supplement": "Ваше дополнение",
        "approve": "Утвердить",
        "reject": "Отклонить",
        "reject_reason": "Причина отклонения",
        "send_approval": "Отправить на согласование",
        "audit_amounts": "Проверка сумм",
        "audit_formulas": "Проверка формул",
        "audit_text": "Проверка текста",
        "audit_layout": "Проверка вёрстки",
        "audit_risk": "Оценка рисков",
        "audit_consistency": "Проверка соответствия",
    },
}


@router.get("/{lang}")
def get_i18n(lang: str):
    """获取指定语言的文案"""
    return DEFAULT_I18N.get(lang, DEFAULT_I18N["zh"])


@router.get("/")
def list_languages():
    """支持的语言列表"""
    return {"languages": list(DEFAULT_I18N.keys())}


@router.put("/{lang}/{key}")
def update_i18n(lang: str, key: str, value: str):
    """更新文案（后台可配置）"""
    if lang not in DEFAULT_I18N:
        DEFAULT_I18N[lang] = {}
    DEFAULT_I18N[lang][key] = value
    return {"lang": lang, "key": key, "value": value}
