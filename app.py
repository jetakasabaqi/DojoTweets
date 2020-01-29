from flask import Flask, render_template, request, redirect, flash, session
from flask_bcrypt import Bcrypt 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import re
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dojo_tweets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key='secret'
bcrypt = Bcrypt(app) 
db=SQLAlchemy(app)
migrate=Migrate(app, db)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')  
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{5,}$')


likes_table=db.Table('likes',
    db.Column("tweet_id", db.Integer, db.ForeignKey("tweets.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column('created_at', db.DateTime, server_default=func.now())
)
followers_table=db.Table('followers',
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("created_at", db.DateTime, server_default=func.now())
)

class User(db.Model):
    __tablename__ = "users"
    id=db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(100))
    last_name=db.Column(db.String(100))
    email=db.Column(db.String(200))
    password_hash=db.Column(db.String(100))
    liked_tweets=db.relationship("Tweet", secondary=likes_table)
    followers=db.relationship("User", 
        secondary=followers_table, 
        primaryjoin=id==followers_table.c.followed_id, 
        secondaryjoin=id==followers_table.c.follower_id,
        backref="following")
    created_at=db.Column(db.DateTime, server_default=func.now())
    updated_at=db.Column(db.DateTime, server_default=func.now(),onupdate=func.now())
    
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    @classmethod
    def add_new_user(cls,data):
        new_user = cls(
            first_name=data['fname'],
            last_name=data['lname'],
            email=data['email'],
            password_hash=bcrypt.generate_password_hash(data['password'])
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @classmethod
    def find_registration_errors(cls, form_data):
        errors=[]
        if len(form_data['fname'])<3:
            errors.append("first name is not long enough")
        if len(form_data['lname'])<3:
            errors.append("last name is not long enough")
        if not EMAIL_REGEX.match(form_data['email']):
            errors.append("invalid email")
        if form_data['password'] != request.form['confirm_password']:
            errors.append("password dont match")
        if len(form_data['password']) < 8:
            errors.append("password isn't long enough")
        return errors

    @classmethod
    def register_new_user(cls, form_data):
        errors = cls.find_registration_errors(form_data)
        valid = len(errors)==0
        data = cls.add_new_user(form_data) if valid else errors
        return {
            "status": "good" if valid else "bad",
            "data": data
        }
class Tweet(db.Model):
    __tablename__="tweets"
    id=db.Column(db.Integer, primary_key=True)
    message=db.Column(db.String(140))
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"))
    author=db.relationship("User", backref="tweets", cascade="all")
    likers=db.relationship("User", secondary=likes_table)
    created_at=db.Column(db.DateTime, server_default=func.now())
    updated_at=db.Column(db.DateTime, server_default=func.now(),onupdate=func.now())

    @classmethod
    def add_new_tweet(cls,tweet):
        db.session.add(tweet)
        db.session.commit()
        return tweet

class Follow(db.Model):
    __tablename__="follows"
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"))
    user=db.relationship("User",backref="likes", cascade="all")
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"))
    user=db.relationship("User",backref="likes", cascade="all")
    created_at=db.Column(db.DateTime, server_default=func.now())

@app.route("/")
def index():
    if 'userid' in session:
        return redirect('/dashboard')  
    else:
        return render_template('index.html')
     

@app.route("/login", methods = ['POST'])
def login():
    user = User.query.filter_by(email = request.form['email']).all()
    valid = True if len(user)==1 and bcrypt.check_password_hash(user[0].password_hash, request.form['password']) else False
    if valid:
        session['userid'] = user[0].id
        return redirect('/dashboard')
    else:
        flash('Invalid login credentials', 'login_error')
        return redirect('/')

@app.route("/get_sign_up")
def load_sign_up():
    if 'userid' in session:
        return redirect('/dashboard')
    else:
        return render_template('sign_up.html')


@app.route('/signup', methods = ['POST'])
def signup():
    result  = User.register_new_user(request.form)
    if result ['status'] == 'good':
        user = result['data']
        session['userid'] = user.id
        return redirect('/dashboard')
    else :
        errors = result['data']
        for error in errors:
            flash(error, 'signup_error')
        return redirect('/get_sign_up')

@app.route('/edit/<tweet_id>')
def get_edit_page(tweet_id):
    tweet = Tweet.query.get(tweet_id)
    return render_template('edit_tweet.html', tweet = tweet)

@app.route('/tweet/edit/<tweet_id>', methods=['POST'])
def edit_tweet(tweet_id):
    tweet = Tweet.query.get(tweet_id)
    if len(request.form['tweet']) > 0:
        tweet.message = request.form['tweet']
        db.session.commit()
        return redirect('/dashboard')
    else:
        flash('Tweets must be between 1 and 255 characters long!','tweet_error') 

    if len(request.form['tweet']) < 1 or len(request.form['tweet']) > 255:
        isValid = False
        flash('Tweets must be between 1 and 255 characters long!','tweet_error')
        return redirect('/edit/'+ tweet_id)

@app.route('/dashboard')
def get_dashboard():
    if 'userid' in session:
        cur_user=User.query.get(session['userid'])
        print(cur_user.following)
        approved_users_ids = [user.id for user in cur_user.following]+[cur_user.id]
        print(approved_users_ids)
        all_tweets=Tweet.query.filter(Tweet.author_id.in_(approved_users_ids)).all()
        liked_tweets =[tweet.id for tweet in cur_user.liked_tweets]
        for tweet in all_tweets:
            time_since_posted = datetime.datetime.now() - tweet.created_at
            days = time_since_posted.days
            hours = time_since_posted.seconds//3600 
            minutes = (time_since_posted.seconds//60)%60
            if days < 0 :
                tweet.time_posted = (0, 0, 0)
            tweet.time_posted = (days, hours, minutes)
            if tweet.id in liked_tweets:
                tweet.already_liked = True
            else:
                tweet.already_liked  = False
            tweet.times_liked = len(tweet.likers)
        
        return render_template("dashboard.html", user = cur_user,tweets=all_tweets)
   
@app.route('/users')
def get_users():
    users = User.query.all()
    user = User.query.get(session['userid'])
    users_followed = [user.id for user in user.following]
    if users_followed:
        for user in users:
            user.followed = False
            if user.id in users_followed:
                user.followed= True
        print(user.followed)
    return render_template('users.html', users = users)



@app.route('/follow/<user_id>')
def follow_user(user_id):
    logges_in_user = User.query.get(session['userid'])
    followed_user = User.query.get(user_id)
    logges_in_user.following.append(followed_user)
    db.session.commit()
    return redirect('/users')

@app.route('/unfollow/<user_id>')
def unfollow_user(user_id):
    logges_in_user = User.query.get(session['userid'])
    followed_user = User.query.get(user_id)
    logges_in_user.following.remove(followed_user)
    db.session.commit()
    return redirect('/users')

@app.route('/logout')
def logout_user():
    session.clear()
    return redirect('/')

@app.route('/tweet/create', methods = ['POST'])
def create_tweet():
    new_tweet = Tweet(message = request.form['tweet'], author_id = session['userid'])
    if len(new_tweet.message) > 0:
        Tweet.add_new_tweet(new_tweet)
    else :
        flash('Tweet must be between 1 and 255 chars long', 'tweet_error')
    return redirect('/dashboard')


@app.route('/tweet/like/<tweet_id>', methods = ['GET'])
def like_tweet(tweet_id):
    print(tweet_id)
    liked_tweet = Tweet.query.get(tweet_id)
    liker = User.query.get(session['userid'])
    liker.liked_tweets.append(liked_tweet)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/tweet/unlike/<tweet_id>')
def unlike_tweet(tweet_id):
    print(tweet_id)
    liked_tweet = Tweet.query.get(tweet_id)
    unliker = User.query.get(session['userid'])
    unliker.liked_tweets.remove(liked_tweet)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/tweet/delete/<tweet_id>')
def delete_tweet(tweet_id):
    tweet_being_deleted = Tweet.query.get(tweet_id)
    tweets_author =tweet_being_deleted.author
    tweets_author.tweets.remove(tweet_being_deleted)
    db.session.commit()
    return redirect('/dashboard')

@app.route("/validate_email", methods = ['POST'])
def validate_email():
    found = False
    print(request.form['email'])
    user = User.query.filter_by(email = request.form['email']).all()
    if user:
        found = True
    print(user)

    print(found)
    return render_template('email_exists.html', found = found)
if __name__== "__main__":
    app.run(debug=True)