from datetime import datetime, timezone
from . import db

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(40), nullable=False)
    daily_limit = db.Column(db.Integer, nullable=False)
    monthly_limit = db.Column(db.Integer, nullable=False)
    price_label = db.Column(db.String(40), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)
    plan = db.relationship("Plan")

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, default="")
    filename = db.Column(db.String(255), nullable=False, unique=True)
    thumbnail_url = db.Column(db.String(500), default="")
    file_size = db.Column(db.Integer, default=0)
    required_plan = db.Column(db.String(20), default="free", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

class DownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False, index=True)
    requested_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="pending", nullable=False)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(500))
    device_id = db.Column(db.String(120))
    browser = db.Column(db.String(100))
    plan_code = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    idempotency_key = db.Column(db.String(100), nullable=False, unique=True)
    failure_reason = db.Column(db.String(250))
    video = db.relationship("Video")
    user = db.relationship("User")

class RegisteredDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    device_id = db.Column(db.String(120), nullable=False)
    label = db.Column(db.String(100), default="Unknown device")
    created_at = db.Column(db.DateTime, default=utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "device_id", name="uq_user_device"),)
