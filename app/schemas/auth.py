from datetime import datetime

from pydantic import BaseModel


# ── 请求 ──

class PhoneLoginRequest(BaseModel):
    phone: str


class CheckPhoneRequest(BaseModel):
    phone: str


class VerifyTokenRequest(BaseModel):
    token: str


# ── 支付 ──

class PaymentProviderRead(BaseModel):
    provider: str
    label: str
    description: str
    qr_svg: str
    amount: str


class PaymentConfigRead(BaseModel):
    wechat: PaymentProviderRead
    alipay: PaymentProviderRead
    customer_service: str


# ── 用户 ──

class SubscriberAccessRead(BaseModel):
    id: str
    phone: str
    payment_status: str
    status: str
    activated_at: str | None = None
    expires_at: str | None = None
    last_login_at: str | None = None


# ── 响应 ──

class PhoneLoginResponse(BaseModel):
    ok: bool
    reason: str | None = None
    message: str
    token: str | None = None
    user: SubscriberAccessRead | None = None
    payment: PaymentConfigRead | None = None


class CheckPhoneResponse(BaseModel):
    allowed: bool
    reason: str | None = None
    message: str
    token: str | None = None
    user: SubscriberAccessRead | None = None
    payment: PaymentConfigRead | None = None


class VerifyTokenResponse(BaseModel):
    ok: bool
    reason: str | None = None
    message: str
    token: str | None = None
    user: SubscriberAccessRead | None = None


class MeResponse(BaseModel):
    id: str
    phone: str
    payment_status: str
    status: str
    activated_at: str | None = None
    expires_at: str | None = None
    last_login_at: str | None = None


class DemoActivateResponse(BaseModel):
    ok: bool
    message: str
    token: str | None = None
    user: SubscriberAccessRead
