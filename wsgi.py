from app import app, db, run_migrations


def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized.")


init_db()
run_migrations()

if __name__ == "__main__":
    app.run()
