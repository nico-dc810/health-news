import hashlib
import hmac
import json
import re
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.subscriber_access import SubscriberAccess

PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
TOKEN_TTL_SECONDS = 86400 * 30

PAYMENT_CONFIG = {
    "wechat": {
        "provider": "wechat",
        "label": "微信支付",
        "description": "请使用微信扫描二维码付款。付款后请联系管理员开通，或点击“我已付款”按钮重新检测。",
        "qr_svg": "/demo/payment-wechat.png",
        "amount": "199 元/年",
    },
    "alipay": {
        "provider": "alipay",
        "label": "支付宝",
        "description": "请使用支付宝扫描二维码付款。付款后请联系管理员开通，或点击“我已付款”按钮重新检测。",
        "qr_svg": "/demo/payment-alipay.png",
        "amount": "199 元/年",
    },
    "customer_service": "付款后如需人工开通，请截屏付款记录联系平台管理员。",
}


def _b64_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return urlsafe_b64decode(data.encode())


def create_session_token(phone: str) -> str:
    payload = json.dumps({"phone": phone, "exp": int(time.time()) + TOKEN_TTL_SECONDS})
    payload_b64 = _b64_encode(payload.encode())
    sig = hmac.new(
        settings.secret_key.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"{payload_b64}.{sig}"


def verify_session_token(token: str) -> dict | None:
    try:
        payload_b64, sig = token.rsplit(".", 1)
        expected = hmac.new(
            settings.secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def require_admin_api_key(api_key: str | None) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="管理员开通密钥尚未配置")
    if not api_key or not hmac.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="管理员密钥无效")


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def validate_phone(phone: str) -> str:
    normalized = normalize_phone(phone)
    if not PHONE_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="请输入有效的 11 位中国大陆手机号")
    return normalized


def password_hash_for_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()


def get_or_create_subscriber(db: Session, phone: str) -> SubscriberAccess:
    subscriber = db.scalar(select(SubscriberAccess).where(SubscriberAccess.phone == phone))
    if subscriber:
        return subscriber

    subscriber = SubscriberAccess(
        phone=phone,
        password_hash=password_hash_for_phone(phone),
        payment_status="pending_payment",
        status="active",
        remark="自助登记",
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


def get_subscriber_by_phone(db: Session, phone: str) -> SubscriberAccess | None:
    return db.scalar(select(SubscriberAccess).where(SubscriberAccess.phone == phone))


def _is_paid_active(subscriber: SubscriberAccess) -> bool:
    if subscriber.status != "active":
        return False
    if subscriber.payment_status != "paid":
        return False
    if subscriber.expires_at is not None:
        now = datetime.now(timezone.utc)
        expires = subscriber.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            return False
    return True


def _subscriber_to_read(subscriber: SubscriberAccess) -> dict:
    return {
        "id": subscriber.id,
        "phone": subscriber.phone,
        "payment_status": subscriber.payment_status,
        "status": subscriber.status,
        "activated_at": subscriber.activated_at.isoformat() if subscriber.activated_at else None,
        "expires_at": subscriber.expires_at.isoformat() if subscriber.expires_at else None,
        "last_login_at": subscriber.last_login_at.isoformat() if subscriber.last_login_at else None,
    }


def check_phone(db: Session, phone: str) -> dict:
    normalized = validate_phone(phone)
    subscriber = get_subscriber_by_phone(db, normalized)

    if subscriber is None:
        return {
            "allowed": False,
            "reason": "new_user",
            "message": "该手机号尚未开通会员，请先扫码付款，再点击“我已付款”按钮进行检测。",
            "payment": PAYMENT_CONFIG,
        }

    if subscriber.status == "blocked":
        return {
            "allowed": False,
            "reason": "blocked",
            "message": "该手机号已被禁用，请联系管理员。",
            "payment": None,
        }

    if _is_paid_active(subscriber):
        token = create_session_token(normalized)
        subscriber.last_login_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "allowed": True,
            "reason": None,
            "message": "验证通过",
            "token": token,
            "user": _subscriber_to_read(subscriber),
            "payment": None,
        }

    reason = "expired" if subscriber.payment_status == "paid" else "unpaid"
    return {
        "allowed": False,
        "reason": reason,
        "message": "该手机号尚未付费或已过期，请付款续费后进入。" if reason == "expired" else "该手机号尚未付款开通。",
        "payment": PAYMENT_CONFIG,
    }


def verify_token(token: str, db: Session) -> dict:
    payload = verify_session_token(token)
    if payload is None:
        return {"ok": False, "reason": "invalid_token", "message": "登录已过期，请重新输入手机号。"}

    phone = payload.get("phone", "")
    subscriber = get_subscriber_by_phone(db, phone)
    if subscriber is None or not _is_paid_active(subscriber):
        return {"ok": False, "reason": "access_revoked", "message": "账号权限已变更，请重新验证。"}

    new_token = create_session_token(phone)
    return {
        "ok": True,
        "reason": None,
        "message": "验证通过",
        "token": new_token,
        "user": _subscriber_to_read(subscriber),
    }


def get_me(db: Session, phone: str) -> dict:
    subscriber = get_subscriber_by_phone(db, phone)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _subscriber_to_read(subscriber)


def login_with_phone(db: Session, phone: str) -> dict:
    normalized = validate_phone(phone)
    subscriber = get_or_create_subscriber(db, normalized)

    if subscriber.status == "blocked":
        return {
            "ok": False,
            "reason": "disabled",
            "message": "该手机号当前不可登录，请联系管理员。",
            "user": _subscriber_to_read(subscriber),
            "payment": None,
            "token": None,
        }

    if not _is_paid_active(subscriber):
        return {
            "ok": False,
            "reason": "unpaid",
            "message": "该手机号尚未付款开通。",
            "user": _subscriber_to_read(subscriber),
            "payment": PAYMENT_CONFIG,
            "token": None,
        }

    token = create_session_token(normalized)
    subscriber.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(subscriber)
    return {
        "ok": True,
        "reason": None,
        "message": "登录成功",
        "token": token,
        "user": _subscriber_to_read(subscriber),
        "payment": None,
    }


def activate_subscriber(
    db: Session,
    phone: str,
    *,
    expires_days: int = 365,
    remark: str | None = None,
) -> dict:
    normalized = validate_phone(phone)
    if expires_days <= 0:
        raise HTTPException(status_code=422, detail="开通天数必须大于 0")

    subscriber = get_or_create_subscriber(db, normalized)
    now = datetime.now(timezone.utc)
    subscriber.payment_status = "paid"
    subscriber.status = "active"
    subscriber.activated_at = subscriber.activated_at or now
    subscriber.expires_at = datetime.fromtimestamp(
        now.timestamp() + 86400 * expires_days, tz=timezone.utc
    )
    subscriber.last_login_at = now
    subscriber.remark = remark or subscriber.remark or "管理员手动开通"
    db.commit()
    db.refresh(subscriber)
    token = create_session_token(normalized)
    return {
        "ok": True,
        "message": "开通成功",
        "token": token,
        "user": _subscriber_to_read(subscriber),
    }


def demo_activate_subscriber(db: Session, phone: str, expires_days: int = 365) -> dict:
    return activate_subscriber(db, phone, expires_days=expires_days)
