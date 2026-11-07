from pathlib import Path
from werkzeug.security import generate_password_hash
from . import db
from .models import User, Plan, Subscription, Video, utcnow

PLANS = [
    ("free", "Free", 1, 5, "Free", 0),
    ("bronze", "Bronze", 3, 30, "₹99/month", 1),
    ("silver", "Silver", 5, 100, "₹199/month", 2),
    ("gold", "Gold", 10, 300, "₹399/month", 3),
]

def seed_data(app):
    with app.app_context():
        db.create_all()
        for code, name, daily, monthly, price, order in PLANS:
            if not Plan.query.filter_by(code=code).first():
                db.session.add(Plan(code=code, name=name, daily_limit=daily,
                                    monthly_limit=monthly, price_label=price, sort_order=order))
        db.session.commit()
        free = Plan.query.filter_by(code="free").first()
        demo = User.query.filter_by(email="demo@streamvault.local").first()
        if not demo:
            demo = User(name="Demo User", email="demo@streamvault.local",
                        password_hash=generate_password_hash("Demo@12345"))
            db.session.add(demo)
            db.session.flush()
            db.session.add(Subscription(user_id=demo.id, plan_id=free.id))
        admin = User.query.filter_by(email="admin@streamvault.local").first()
        if not admin:
            db.session.add(User(name="StreamVault Admin", email="admin@streamvault.local",
                password_hash=generate_password_hash("Admin@12345"), role="admin"))
        video_dir = Path(app.config["VIDEO_STORAGE_PATH"])
        video_dir.mkdir(parents=True, exist_ok=True)
        samples = [
            ("Welcome to StreamVault", "A short sample video entry. Replace the sample media with your own licensed MP4.", "sample-welcome.mp4", "free"),
            ("Python Fundamentals", "A learning video for subscribers.", "python-fundamentals.mp4", "bronze"),
            ("Full Stack Architecture", "A deeper full-stack engineering lesson.", "fullstack-architecture.mp4", "silver"),
            ("Advanced System Design", "Premium system design content.", "system-design.mp4", "gold"),
        ]
        for title, desc, filename, required in samples:
            if not Video.query.filter_by(filename=filename).first():
                path = video_dir / filename
                size = path.stat().st_size if path.exists() else 0
                db.session.add(Video(title=title, description=desc, filename=filename,
                    thumbnail_url="", file_size=size, required_plan=required))
        db.session.commit()
