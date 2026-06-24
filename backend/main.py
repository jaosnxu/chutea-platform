"""
合同审核平台 — FastAPI 后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.contracts import router as contracts_router
from api.i18n import router as i18n_router
from api.approvals import router as approvals_router

app = FastAPI(title="Contract Review Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(contracts_router)
app.include_router(i18n_router)
app.include_router(approvals_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "contract-review-platform"}


@app.get("/health")
def health():
    return {"status": "healthy"}
