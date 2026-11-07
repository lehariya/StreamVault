from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..models import Video
from ..services import active_plan, PLAN_RANK

catalog_bp = Blueprint("catalog", __name__)

@catalog_bp.get("")
@jwt_required()
def list_videos():
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    plan, _ = active_plan(user_id)
    items = []
    for v in Video.query.filter_by(is_active=True).order_by(Video.id).all():
        items.append({"id":v.id,"title":v.title,"description":v.description,
            "thumbnail_url":v.thumbnail_url,"file_size":v.file_size,
            "required_plan":v.required_plan,
            "accessible":PLAN_RANK.get(plan.code,0) >= PLAN_RANK.get(v.required_plan,0)})
    return jsonify(items)
