from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models import User, Plan, Subscription
from ..services import active_plan, quota_snapshot

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name, email, password = (data.get("name","").strip(), data.get("email","").strip().lower(), data.get("password",""))
    if not name or len(name) > 100 or "@" not in email or len(password) < 8:
        return jsonify({"error":"Enter a name, valid email, and password of at least 8 characters."}), 400
    user = User(name=name, email=email, password_hash=generate_password_hash(password))
    try:
        db.session.add(user); db.session.flush()
        free = Plan.query.filter_by(code="free").first()
        db.session.add(Subscription(user_id=user.id, plan_id=free.id))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error":"An account with this email already exists."}), 409
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token":token, "user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}}), 201

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=data.get("email","").strip().lower()).first()
    if not user or not check_password_hash(user.password_hash, data.get("password","")):
        return jsonify({"error":"Invalid email or password."}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token":token, "user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}})

@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user: return jsonify({"error":"User not found"}), 404
    plan, sub = active_plan(user.id)
    return jsonify({"id":user.id,"name":user.name,"email":user.email,"role":user.role,
                    "subscription":{"plan":plan.code,"name":plan.name,"expires_at":sub.expires_at.isoformat() if sub and sub.expires_at else None},
                    "quota":quota_snapshot(user.id, plan)})
