from flask import Flask, jsonify, url_for, request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import uuid


app = Flask(__name__)
app.secret_key = 'hahahahahahahahahhahano'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.debug = True
db = SQLAlchemy(app)


@app.after_request
def make_jsonapi(response):
    response.headers['Content-Type'] = 'application/vnd.api+json'
    return response


class ConflictError(Exception):
    def __init__(self):
        self.resp = Response({})
        self.resp.status = 'Conflict'
        self.resp.status_code = 409


class User(db.Model):
    id = db.Column(db.String, primary_key=True, autoincrement=False)
    url = db.Column(db.String(), unique=True)
    password = db.Column(db.String(36), unique=True)

    def __init__(self, id, url):
        self.id = id
        self.url = url
        self.password = str(uuid.uuid4())

    def __repr__(self):
        return self.id

    def json(self):
        return {
                'data': {
                    'type': 'users',
                    'attributes': {
                        'username': self.id, 
                        'url': self.url
                        }
                    },
                'links': {
                    'self': url_for('get_user', 
                        username=self.id, _external=True),
                    'related': url_for('get_user_tweets', 
                        username=self.id, _external=True)
                    }
                }


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.String())
    body = db.Column(db.String())

    user_id = db.Column(db.String, db.ForeignKey('user.id'))
    user = db.relationship('User',
        backref=db.backref('tweets', lazy='dynamic'))

    def __init__(self, user_id, datetime, body):
        self.user_id = user_id
        self.datetime = datetime
        self.body = body

    def __repr__(self):
        return str(self.id)

    def json(self):
        return {
                'data': {
                    'type': 'tweets',
                    'id': self.id,
                    'attributes': {
                        'username': self.user_id,
                        'datetime': self.datetime, 
                        'body': self.body
                        }
                    },
                'links': {
                    'self': url_for('get_tweet',
                        username=self.user.id,
                        tweet=self.id, 
                        _external=True),
                    'related': url_for('get_user_tweets',
                        username=self.user_id, _external=True)
                    }
                }


@app.route('/users', methods=['GET', 'POST'])
def get_users():
    if request.method == 'POST':
        try:
            if request.get_json()['data']['type'] != 'users':
                raise ConflictError
            r = request.get_json()['data']['attributes']
            u = User(id=r['username'], url=r['url'])

            db.session.add(u)
            db.session.commit()

            resp = Response({})
            resp.status = 'Created'
            resp.status_code = 201
            return resp
        except IntegrityError:
            resp = Response({})
            resp.status = 'Conflict'
            resp.status_code = 409
            return resp
        except ConflictError as e:
            return e.resp
    else:
        users = User.query.all()
        return jsonify({
            'links': {
                'self': url_for('get_users', _external=True)
                },
            'data': [x.json() for x in users]
            })


@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(id=username).first_or_404()
    return jsonify(user.json())


@app.route('/users/<username>/tweets', methods=['GET'])
def get_user_tweets(username):
    user = User.query.filter_by(id=username).first_or_404()
    tweets = user.tweets.all()
    return jsonify({                                                            
        'links': {                                                              
            'self': url_for('get_user_tweets', 
                username=user.id, _external=True),
            'related': url_for('get_user',
                username=username, _external=True)
            },                                                                  
        'data': [x.json() for x in tweets]                                      
        })


@app.route('/tweets', methods=['GET'])
def get_tweets():
    tweets = Tweet.query.all()
    return jsonify({                                                        
        'links': {                                                          
            'self': url_for('get_tweets', _external=True)                    
            },                                                              
        'data': [x.json() for x in tweets]
        })


@app.route('/users/<username>/tweets/<tweet>', methods=['GET'])
def get_tweet(username, tweet):
    user = User.query.filter_by(id=username).first_or_404()
    tweet = user.tweets.filter_by(id=tweet).first_or_404()
    return jsonify(tweet.json())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
