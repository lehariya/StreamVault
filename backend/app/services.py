from datetime import datetime, timezone
from sqlalchemy import func
from . import db
from .models import Plan, Subscription, DownloadRecord, RegisteredDevice, utcnow

PLAN_RANK = {"free": 0, "bronze": 1, "silver": 2, "gold": 3}

def active_plan(user_id):
    now = utcnow()
    sub = (Subscription.query.filter_by(user_id=user_id, status="active")
           .filter(Subscription.starts_at <= now)
           .filter((Subscription.expires_at.is_(None)) | (Subscription.expires_at > now))
           .order_by(Subscription.starts_at.desc()).first())
    if sub:
        return sub.plan, sub
    return Plan.query.filter_by(code="free").first(), None

def quota_snapshot(user_id, plan=None, now=None):
    now = now or utcnow()
    plan = plan or active_plan(user_id)[0]
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Pending reservations count too, so concurrent requests cannot exceed a quota.
    used_day = DownloadRecord.query.filter(
        DownloadRecord.user_id == user_id,
        DownloadRecord.requested_at >= day_start,
        DownloadRecord.status.in_(["pending", "completed"])
    ).count()
    used_month = DownloadRecord.query.filter(
        DownloadRecord.user_id == user_id,
        DownloadRecord.requested_at >= month_start,
        DownloadRecord.status.in_(["pending", "completed"])
    ).count()
    return {
        "plan": plan.code, "plan_name": plan.name,
        "daily_limit": plan.daily_limit, "monthly_limit": plan.monthly_limit,
        "used_today": used_day, "used_this_month": used_month,
        "remaining_today": max(0, plan.daily_limit - used_day),
        "remaining_this_month": max(0, plan.monthly_limit - used_month),
        "reset_daily_at": (day_start.replace(tzinfo=timezone.utc).timestamp() + 86400),
    }

def user_has_device(user_id, device_id):
    if not device_id:
        return False
    return RegisteredDevice.query.filter_by(user_id=user_id, device_id=device_id).first() is not None

def browser_name(user_agent):
    ua = (user_agent or "").lower()
    if "edg/" in ua: return "Edge"
    if "chrome/" in ua: return "Chrome"
    if "firefox/" in ua: return "Firefox"
    if "safari/" in ua: return "Safari"
    return "Unknown"
