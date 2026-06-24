"""
审批流状态机 + API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


# ====== Enums ======
class ApprovalNodeType(str, Enum):
    approver = "approver"      # 必须审批
    cc = "cc"                  # 抄送（只通知）
    initiator_choice = "initiator_choice"  # 发起人自选


class ApprovalMethod(str, Enum):
    sequential = "sequential"  # 依次审批
    parallel = "parallel"      # 并行审批
    or_sign = "or_sign"        # 或签（任一人通过）


class ApprovalStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    approved = "approved"
    rejected = "rejected"
    revised = "revised"        # 驳回后重新提交
    cancelled = "cancelled"


# ====== Models ======
class ApprovalNode(BaseModel):
    order: int
    node_type: ApprovalNodeType
    approver_id: Optional[str] = None
    approver_name: str


class ApprovalTemplate(BaseModel):
    id: str
    name: str
    nodes: List[ApprovalNode]
    method: ApprovalMethod = ApprovalMethod.sequential
    timeout_hours: int = 48  # 超时自动升级


class ApprovalInstance(BaseModel):
    id: str
    template_id: str
    business_type: str  # "contract_review"
    business_id: str
    status: ApprovalStatus = ApprovalStatus.pending
    current_step: int = 0
    created_at: str = ""
    created_by: str = ""
    summary: Optional[str] = None  # AI 摘要卡


class ApprovalAction(BaseModel):
    instance_id: str
    action: Literal["approve", "reject"]
    comment: str = ""
    user_id: str


# ====== Storage (dev) ======
_templates: dict = {}
_instances: dict = {}
_users: dict = {
    "awan": {"id": "awan", "name": "阿万", "role": "admin"},
    "jason": {"id": "jason", "name": "Jason", "role": "approver"},
    "ceo": {"id": "ceo", "name": "CEO", "role": "approver"},
}


# ====== API ======
@router.get("/templates")
def list_templates():
    return list(_templates.values())


@router.post("/templates")
def create_template(template: ApprovalTemplate):
    _templates[template.id] = template.model_dump()
    return {"status": "created", "id": template.id}


@router.get("/templates/{template_id}")
def get_template(template_id: str):
    return _templates.get(template_id, {})


@router.post("/instances")
def create_instance(instance: ApprovalInstance):
    template = _templates.get(instance.template_id)
    if not template:
        return {"error": "template not found"}
    instance.id = instance.id or f"apv-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    instance.status = ApprovalStatus.pending
    instance.current_step = 0
    instance.created_at = datetime.now().isoformat()
    _instances[instance.id] = instance.model_dump()
    # 自动推进到第一个审批节点
    _instances[instance.id]["status"] = ApprovalStatus.in_progress
    _instances[instance.id]["current_step"] = 0
    return _instances[instance.id]


@router.get("/instances/{instance_id}")
def get_instance(instance_id: str):
    return _instances.get(instance_id, {})


@router.get("/instances")
def list_instances(user_id: str = "", status: str = ""):
    result = list(_instances.values())
    if user_id:
        result = [i for i in result if i["created_by"] == user_id]
    if status:
        result = [i for i in result if i["status"] == status]
    return result


@router.post("/instances/{instance_id}/action")
def process_action(instance_id: str, action: ApprovalAction):
    instance = _instances.get(instance_id)
    if not instance:
        return {"error": "instance not found"}

    template = _templates.get(instance["template_id"])
    if not template:
        return {"error": "template not found"}

    nodes = template["nodes"]
    current_step = instance["current_step"]
    current_node = nodes[current_step]

    # 验证审批人
    if current_node["node_type"] == "approver" and current_node["approver_id"] != action.user_id:
        return {"error": f"审批人应为 {current_node['approver_name']}"}

    if action.action == "approve":
        # 推进到下一节点
        next_step = current_step + 1
        if next_step >= len(nodes):
            instance["status"] = ApprovalStatus.approved
            instance["current_step"] = next_step
        else:
            instance["current_step"] = next_step
    elif action.action == "reject":
        instance["status"] = ApprovalStatus.rejected
        instance["current_step"] = 0  # 退回到发起人
        instance["reject_reason"] = action.comment

    _instances[instance_id] = instance
    return instance


@router.post("/instances/{instance_id}/resubmit")
def resubmit(instance_id: str):
    """驳回后重新提交"""
    instance = _instances.get(instance_id)
    if not instance:
        return {"error": "instance not found"}
    instance["status"] = ApprovalStatus.revised
    instance["current_step"] = 0
    _instances[instance_id] = instance
    return instance


@router.get("/users")
def list_users():
    return list(_users.values())


@router.post("/instances/{instance_id}/summary")
def update_summary(instance_id: str, summary: str):
    """AI 摘要卡"""
    instance = _instances.get(instance_id)
    if instance:
        instance["summary"] = summary
    return instance
