#!/bin/sh

python << END
from app import app, db
with app.app_context():
    db.create_all()
END

exec gunicorn --bind 0.0.0.0:5000 app:app