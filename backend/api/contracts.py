"""
合同审核 API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
import json

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/Users/xuyongwenmacbookpro/workspace/p002-contract-platform/data")
STORAGE_FILE = os.path.join(UPLOAD_DIR, "contracts.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)

def _load():
    if not os.path.exists(STORAGE_FILE):
        return []
    with open(STORAGE_FILE) as f:
        return json.load(f)

def _save(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ReviewRequest(BaseModel):
    contract_id: int
    selections: dict  # {clause_id: "A"|"B"}


class ApprovalRequest(BaseModel):
    contract_id: int
    step: int
    action: str  # approve / reject
    comment: str = ""


class ContractSave(BaseModel):
    id: str
    name: str
    content: str = ""
    status: str = "draft"
    selections: dict = {}
    notes: dict = {}
    approval_status: str = ""
    approval_id: str = ""


@router.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    """上传合同文件"""
    content = await file.read()
    return {
        "filename": file.filename,
        "size": len(content),
        "status": "uploaded",
        "uploaded_at": datetime.now().isoformat(),
    }


@router.post("/save")
def save_contract(contract: ContractSave):
    """保存合同到本地 JSON"""
    all_contracts = _load()
    # 更新或新增
    for i, c in enumerate(all_contracts):
        if c["id"] == contract.id:
            all_contracts[i] = contract.model_dump()
            _save(all_contracts)
            return {"status": "updated", "id": contract.id}
    all_contracts.append(contract.model_dump())
    _save(all_contracts)
    return {"status": "saved", "id": contract.id}


@router.get("/list")
def list_contracts():
    """获取所有已保存的合同"""
    return _load()


@router.get("/{contract_id}")
def get_contract(contract_id: str):
    """获取单个合同"""
    all_contracts = _load()
    for c in all_contracts:
        if c["id"] == contract_id:
            return c
    return {}


@router.delete("/{contract_id}")
def delete_contract(contract_id: str):
    """删除合同"""
    all_contracts = _load()
    all_contracts = [c for c in all_contracts if c["id"] != contract_id]
    _save(all_contracts)
    return {"status": "deleted", "id": contract_id}


@router.post("/{contract_id}/analyze")
async def analyze_contract(contract_id: int):
    return {"status": "analyzing", "contract_id": contract_id}


@router.post("/{contract_id}/select")
async def select_options(contract_id: int, req: ReviewRequest):
    return {"status": "rewriting", "contract_id": contract_id, "selections": req.selections}


@router.get("/{contract_id}/audit")
async def second_audit(contract_id: int):
    return {"status": "audited", "contract_id": contract_id}


@router.post("/{contract_id}/approve")
async def approve_contract(contract_id: int, req: ApprovalRequest):
    return {"status": req.action, "contract_id": contract_id, "step": req.step, "comment": req.comment}
