"""
数据库模型 — SQLAlchemy + PostgreSQL
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/contract_platform")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True)
    role = Column(String(50), default="reviewer")  # admin / reviewer / approver
    language = Column(String(10), default="zh")  # zh / ru


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    content = Column(Text)  # 合同全文
    contract_type = Column(String(100), default="sublicense")  # sublicense / renovation / supply
    language = Column(String(10), default="ru")
    status = Column(String(50), default="uploaded")  # uploaded / analyzing / reviewed / rewritten / audited / approved
    created_at = Column(DateTime)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    review_type = Column(String(50))  # first_audit / rewrite / second_audit
    content = Column(JSON)  # 审核结果（3方案 / 改写 / 2审）
    status = Column(String(50), default="pending")
    contract = relationship("Contract", backref="reviews")


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    step = Column(Integer)  # 审批步骤序号
    approver_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="pending")  # pending / approved / rejected
    comment = Column(Text)
    contract = relationship("Contract", backref="approvals")


class I18n(Base):
    __tablename__ = "i18n"
    id = Column(Integer, primary_key=True)
    key = Column(String(200), nullable=False)
    lang = Column(String(10), nullable=False)  # zh / ru
    value = Column(Text, nullable=False)


class ApprovalConfig(Base):
    """审批流配置 — 钉钉式拖拽"""
    __tablename__ = "approval_configs"
    id = Column(Integer, primary_key=True)
    contract_type = Column(String(100))
    steps = Column(JSON)  # [{order:1, approver_id:N, review_scope:"3options"}]


def init_db():
    Base.metadata.create_all(bind=engine)
