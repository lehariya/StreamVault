from pathlib import Path
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models import User, Video, Plan, Subscription

admin_bp=Blueprint("admin",__name__)

def admin_only():
    user=db.session.get(User,int(get_jwt_identity()))
    return user if user and user.role=="admin" else None

@admin_bp.get("/downloads")
@jwt_required()
def audit_downloads():
    if not admin_only(): return jsonify({"error":"Administrator access required."}),403
    from ..models import DownloadRecord
    rows=DownloadRecord.query.order_by(DownloadRecord.requested_at.desc()).limit(500).all()
    return jsonify([{"id":r.id,"user_id":r.user_id,"email":r.user.email,"video_id":r.video_id,
        "video_title":r.video.title,"timestamp":r.requested_at.isoformat(),"status":r.status,
        "ip_address":r.ip_address,"device_id":r.device_id,"browser":r.browser,"plan":r.plan_code}
        for r in rows])

@admin_bp.post("/videos")
@jwt_required()
def create_video():
    if not admin_only(): return jsonify({"error":"Administrator access required."}),403
    data=request.get_json(silent=True) or {}
    required=("title","filename","required_plan")
    if any(not data.get(k) for k in required): return jsonify({"error":"title, filename and required_plan are required."}),400
    if data["required_plan"] not in ("free","bronze","silver","gold"): return jsonify({"error":"Invalid plan."}),400
    filename=Path(data["filename"]).name
    path=Path(current_app.config["VIDEO_STORAGE_PATH"])/filename
    size=path.stat().st_size if path.exists() else 0
    video=Video(title=data["title"][:180],description=data.get("description",""),
        filename=filename,thumbnail_url=data.get("thumbnail_url",""),
        file_size=size,required_plan=data["required_plan"])
    db.session.add(video); db.session.commit()
    return jsonify({"id":video.id,"message":"Video created."}),201
