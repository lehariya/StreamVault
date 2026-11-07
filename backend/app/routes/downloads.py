import os, uuid
from threading import RLock
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app, send_file, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models import Video, DownloadRecord, RegisteredDevice
from ..services import active_plan, quota_snapshot, PLAN_RANK, browser_name, user_has_device

downloads_bp = Blueprint("downloads", __name__)
# Serializes quota reservation within this API process. Multi-process deployments
# must replace this with database-level atomic locking/reservation.
reservation_lock = RLock()

def authorization_error(uid, video, device_id):
    plan, sub = active_plan(uid)
    if not video or not video.is_active:
        return "Video is unavailable.", 404
    if PLAN_RANK.get(plan.code,0) < PLAN_RANK.get(video.required_plan,0):
        return "Your current plan does not include access to this video.", 403
    if current_app.config["DEVICE_LIMIT_ENABLED"] and not user_has_device(uid, device_id):
        return "This device is not registered to your account.", 403
    quota=quota_snapshot(uid,plan)
    if quota["remaining_today"] <= 0:
        return "Daily download quota exhausted.", 429
    if quota["remaining_this_month"] <= 0:
        return "Monthly download quota exhausted.", 429
    path=Path(current_app.config["VIDEO_STORAGE_PATH"]) / video.filename
    if not path.is_file():
        return "Video file is not available on the server. Ask an administrator to upload it.", 404
    return None

@downloads_bp.get("/quota")
@jwt_required()
def quota():
    uid=int(get_jwt_identity()); plan,_=active_plan(uid)
    return jsonify(quota_snapshot(uid,plan))

@downloads_bp.post("/authorize")
@jwt_required()
def authorize():
    uid=int(get_jwt_identity()); data=request.get_json(silent=True) or {}
    video=db.session.get(Video,data.get("video_id"))
    err=authorization_error(uid,video,data.get("device_id"))
    if err:
        message,status=err
        return jsonify({"authorized":False,"error":message}),status
    plan,_=active_plan(uid)
    return jsonify({"authorized":True,"video_id":video.id,"plan":plan.code,
                    "quota":quota_snapshot(uid,plan)})

@downloads_bp.post("/<int:video_id>")
@jwt_required()
def download(video_id):
    uid=int(get_jwt_identity()); data=request.get_json(silent=True) or {}
    key=request.headers.get("Idempotency-Key") or data.get("idempotency_key")
    if not key or len(key)>100:
        return jsonify({"error":"A valid Idempotency-Key header is required."}),400
    existing=DownloadRecord.query.filter_by(idempotency_key=key).first()
    if existing:
        if existing.user_id != uid or existing.video_id != video_id:
            return jsonify({"error":"Idempotency key conflict."}),409
        if existing.status == "completed":
            return jsonify({"message":"This download was already completed.","download_id":existing.id}),200
        if existing.status == "pending":
            return jsonify({"error":"This download is already in progress.","download_id":existing.id}),409
    with reservation_lock:
        video=db.session.get(Video,video_id)
        device_id=(data.get("device_id") or "")[:120]
        err=authorization_error(uid,video,device_id)
        if err:
            message,status=err
            return jsonify({"error":message}),status
        plan,_=active_plan(uid)
        ua=request.headers.get("User-Agent","")
        record=DownloadRecord(user_id=uid,video_id=video.id,ip_address=request.remote_addr,
            user_agent=ua[:500],device_id=device_id or None,browser=browser_name(ua),
            plan_code=plan.code,file_size=video.file_size,idempotency_key=key,status="pending")
        try:
            db.session.add(record); db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error":"A simultaneous request used this download key. Refresh your downloads."}),409
    path=Path(current_app.config["VIDEO_STORAGE_PATH"]) / video.filename
    response=send_file(path,as_attachment=True,download_name=video.filename,conditional=True)
    response.headers["X-Download-Record-Id"]=str(record.id)
    response.headers["Cache-Control"]="no-store"
    # WSGI close is called after response iteration; a fully consumed response is marked complete.
    original_close=response.close
    def close_and_mark():
        try:
            original_close()
            rec=db.session.get(DownloadRecord,record.id)
            if rec and rec.status=="pending":
                rec.status="completed"; rec.completed_at=datetime.utcnow(); db.session.commit()
        except Exception:
            db.session.rollback()
            rec=db.session.get(DownloadRecord,record.id)
            if rec and rec.status=="pending":
                rec.status="failed"; rec.failure_reason="Response stream did not complete"; db.session.commit()
        finally:
            db.session.remove()
    response.call_on_close(close_and_mark)
    return response

@downloads_bp.get("/history")
@jwt_required()
def history():
    uid=int(get_jwt_identity())
    rows=DownloadRecord.query.filter_by(user_id=uid).order_by(DownloadRecord.requested_at.desc()).limit(200).all()
    return jsonify([{"id":r.id,"video_id":r.video_id,"title":r.video.title,
        "thumbnail_url":r.video.thumbnail_url,"downloaded_at":r.completed_at.isoformat() if r.completed_at else r.requested_at.isoformat(),
        "status":r.status,"file_size":r.file_size,"plan":r.plan_code,
        "ip_address":r.ip_address,"device_id":r.device_id,"browser":r.browser,
        "failure_reason":r.failure_reason} for r in rows])

@downloads_bp.post("/devices")
@jwt_required()
def register_device():
    uid=int(get_jwt_identity()); data=request.get_json(silent=True) or {}
    device_id=(data.get("device_id") or "").strip()
    if not device_id or len(device_id)>120: return jsonify({"error":"Provide a device_id up to 120 characters."}),400
    existing=RegisteredDevice.query.filter_by(user_id=uid,device_id=device_id).first()
    if not existing:
        db.session.add(RegisteredDevice(user_id=uid,device_id=device_id,label=(data.get("label") or "My device")[:100]))
        db.session.commit()
    return jsonify({"message":"Device registered."}),201
