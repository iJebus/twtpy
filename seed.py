from app import db, User, Tweet
from datetime import datetime

def seed():
    db.drop_all()
    db.create_all()

    x = User('ijebus', 'http://diary.ljones.id.au')
    db.session.add(x)
    db.session.commit()

    y = Tweet('ijebus', datetime.utcnow().isoformat(), 'Love cheese!')
    db.session.add(y)
    db.session.commit()

