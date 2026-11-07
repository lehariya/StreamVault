from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import timedelta
from .. import db
from ..models import Plan, Subscription
from ..services import active_plan, quota_snapshot

subscriptions_bp = Blueprint("subscriptions", __name__)

@subscriptions_bp.get("/plans")
@jwt_required()
def plans():
    return jsonify([{"code":p.code,"name":p.name,"daily_limit":p.daily_limit,
                     "monthly_limit":p.monthly_limit,"price_label":p.price_label}
                    for p in Plan.query.order_by(Plan.sort_order).all()])

@subscriptions_bp.get("/me")
@jwt_required()
def my_subscription():
    uid=int(get_jwt_identity()); plan, sub=active_plan(uid)
    return jsonify({"plan":plan.code,"plan_name":plan.name,
        "starts_at":sub.starts_at.isoformat() if sub else None,
        "expires_at":sub.expires_at.isoformat() if sub and sub.expires_at else None,
        "quota":quota_snapshot(uid,plan)})

@subscriptions_bp.post("/activate-demo")
@jwt_required()
def activate_demo():
    # Demo-only subscription activation. Production must integrate a verified payment webhook.
    data=request.get_json(silent=True) or {}; code=data.get("plan")
    if code not in ("bronze","silver","gold"):
        return jsonify({"error":"Choose Bronze, Silver, or Gold."}),400
    uid=int(get_jwt_identity()); plan=Plan.query.filter_by(code=code).first()
    current, old=active_plan(uid)
    if old:
        old.status="expired"
    db.session.add(Subscription(user_id=uid,plan_id=plan.id,expires_at=__import__("datetime").datetime.utcnow()+timedelta(days=30)))
    db.session.commit()
    return jsonify({"message":f"{plan.name} demo subscription activated for 30 days.",
                    "plan":plan.code,"quota":quota_snapshot(uid,plan)})
