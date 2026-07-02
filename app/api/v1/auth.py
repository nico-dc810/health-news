from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    CheckPhoneRequest,
    CheckPhoneResponse,
    DemoActivateResponse,
    MeResponse,
    PaymentConfigRead,
    PhoneLoginRequest,
    PhoneLoginResponse,
    VerifyTokenRequest,
    VerifyTokenResponse,
)
from app.services.subscriber_auth import (
    PAYMENT_CONFIG,
    check_phone,
    create_session_token,
    demo_activate_subscriber,
    get_me,
    login_with_phone,
    verify_session_token,
    verify_token,
)

router = APIRouter()


# ── 原有端点（向后兼容） ──

@router.post("/phone-login", response_model=PhoneLoginResponse)
def phone_login(payload: PhoneLoginRequest, db: Session = Depends(get_db)) -> dict:
    return login_with_phone(db, payload.phone)


@router.post("/demo-activate", response_model=DemoActivateResponse)
def demo_activate(payload: PhoneLoginRequest, db: Session = Depends(get_db)) -> dict:
    return demo_activate_subscriber(db, payload.phone)


@router.get("/payment-config", response_model=PaymentConfigRead)
def payment_config() -> dict:
    return PAYMENT_CONFIG


# ── 新增端点：两阶段登录核心 ──

@router.post("/check-phone", response_model=CheckPhoneResponse)
def api_check_phone(payload: CheckPhoneRequest, db: Session = Depends(get_db)) -> dict:
    """检查手机号状态：已付款→返回 token，未付款→返回支付信息"""
    return check_phone(db, payload.phone)


# ── 新增端点：Token 验证与续期 ──

@router.post("/verify-token", response_model=VerifyTokenResponse)
def api_verify_token(payload: VerifyTokenRequest, db: Session = Depends(get_db)) -> dict:
    """验证已有 token 是否有效，有效则续期"""
    return verify_token(payload.token, db)


# ── 新增端点：获取当前用户信息 ──

@router.get("/me", response_model=MeResponse)
def api_me(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
) -> dict:
    """从 Bearer token 获取当前用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_session_token(token)
    if payload is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    phone = payload.get("phone", "")
    return get_me(db, phone)
