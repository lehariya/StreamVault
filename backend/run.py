from app import create_app, db
from app.seed import seed_data
app=create_app()
with app.app_context():
    db.create_all()
if __name__=="__main__":
    seed_data(app)
    app.run(host="127.0.0.1",port=5000,debug=True)
