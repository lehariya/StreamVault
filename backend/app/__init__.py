import os
from pathlib import Path
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

db = SQLAlchemy()
jwt = JWTManager()

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    base_dir = Path(__file__).resolve().parent.parent
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{base_dir / 'streamvault.db'}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        VIDEO_STORAGE_PATH=os.getenv("VIDEO_STORAGE_PATH", str(base_dir / "storage" / "videos")),
        DEVICE_LIMIT_ENABLED=os.getenv("DEVICE_LIMIT_ENABLED", "false").lower() == "true",
    )
    if test_config:
        app.config.update(test_config)
    CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
         supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    from .routes.auth import auth_bp
    from .routes.catalog import catalog_bp
    from .routes.subscriptions import subscriptions_bp
    from .routes.downloads import downloads_bp
    from .routes.admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(catalog_bp, url_prefix="/api/videos")
    app.register_blueprint(subscriptions_bp, url_prefix="/api/subscriptions")
    app.register_blueprint(downloads_bp, url_prefix="/api/downloads")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "StreamVault API"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Unexpected server error"}), 500

    return app
