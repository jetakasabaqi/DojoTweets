from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt 
import re
import datetime
app = Flask(__name__)
app.secret_key='secret'
bcrypt = Bcrypt(app) 
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')  
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{5,}$')
@app.route("/")
def index():
    if 'userid' in session:
        return redirect('/dashboard')  
    else:
        return render_template('index.html')
     

@app.route("/login", methods = ['POST'])
def login():
    isValid = True
    # Validate email and password 
    if not EMAIL_REGEX.match(request.form['email']):   
        isValid = False
        flash("Invalid email address format!",'email_error')
    if len(request.form['password']) < 5:
        isValid = False
        flash("Password should be longer than 5 characters",'password_error')

    if isValid:
        data ={
        'email': request.form['email'],
        'psw': request.form['password'] 
        } 
        mysql = connectToMySQL("dojo_tweets")
        query = "SELECT * FROM users WHERE email = %(email)s;"
        result = mysql.query_db(query, data)
        if result:
            if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
                session['userid'] = result[0]['id']
                return redirect('/dashboard')
        flash("Password or Email is wrong", 'login_error')
    return redirect('/')


@app.route("/get_sign_up")
def load_sign_up():
    if 'userid' in session:
        return redirect('/dashboard')
    else:
        return render_template('sign_up.html')


@app.route('/signup', methods = ['POST'])
def signup():
    isValid = True
    
    if len(request.form['fname']) < 1:
    	isValid = False
    	flash("Please enter a first name",'name_error')
    if not (request.form['fname']).isalpha():
    	isValid = False
    	flash("First Name must only contain letters!",'name_error')
    if len(request.form['lname']) < 1:
    	isValid = False
    	flash("Please enter a last name",'last_error')
    if not (request.form['lname']).isalpha():
    	isValid = False
    	flash("Last Name must only contain letters!",'last_error')
    if not EMAIL_REGEX.match(request.form['email']):   
        isValid = False
        flash("Invalid email address!",'email_error')
    if not PASSWORD_REGEX.match(request.form['password']):   
        isValid = False
        flash("Password must have at least 5 characters, one number, one uppercase character, one special symbol.",'psw_error')
    if request.form['password'] != request.form['confirm_password']:
    	isValid = False
    	flash("Password and Confirm Password should match",'confirm_psw_error')
    
    if isValid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])  
        data ={
        'fname': request.form['fname'],
        'lname': request.form['lname'],
        'email': request.form['email'],
        'psw': pw_hash,
        'created_at': datetime.datetime.now(),
        'updated_at': datetime.datetime.now()
        }

        mysql = connectToMySQL("dojo_tweets")
        query = "INSERT into users (fname,lname,email,password,created_at, updated_at) values(%(fname)s,%(lname)s,%(email)s,%(psw)s,%(created_at)s,%(updated_at)s);"
        result = mysql.query_db(query, data)
        print(result)
        if result:
            session['userid'] = result
            return redirect('/dashboard')
        flash("Could not sign up, please try again", 'signup_error')

    return redirect('/get_sign_up')

@app.route('/edit/<tweet_id>')
def get_edit_page(tweet_id):
    mysql = connectToMySQL("dojo_tweets")
    query = f"select * from tweets where tweets.id = {tweet_id};"
    result = mysql.query_db(query)
    tweet = None
    print('get edit page', tweet_id)
    if result:
        tweet = result[0]
    print(tweet)
    return render_template('edit_tweet.html', tweet = tweet)

@app.route('/tweet/edit/<tweet_id>', methods=['POST'])
def edit_tweet(tweet_id):
    isValid = True
    if len(request.form['tweet']) < 1 or len(request.form['tweet']) > 255:
        isValid = False
        flash('Tweets must be between 1 and 255 characters long!','tweet_error') 
   
    if isValid:
        data = {
            'tweet_id': tweet_id,
            'tweet': request.form['tweet'],
            'updated_at': datetime.datetime.now()
        }
        mysql = connectToMySQL("dojo_tweets")
        query = 'update tweets set tweets.content = %(tweet)s , tweets.updated_at = %(updated_at)s where tweets.id = %(tweet_id)s;'
        result = mysql.query_db(query,data)
        return redirect('/dashboard')
    return redirect('/edit/'+ tweet_id)
@app.route('/dashboard')
def get_dashboard():
    if 'userid' in session:
        mysql = connectToMySQL("dojo_tweets")
        query = f'select * from users where users.id = {session["userid"]}'
        result = mysql.query_db(query)
        user = ''
        if result:
            user = result[0]['fname']
       
       
        mysql = connectToMySQL("dojo_tweets")
        data ={
        'user_id': session['userid']
            } 
        query = 'select  tweets.content as tweet, users.fname as username, tweets.created_at as time_posted,tweets.id as tweet_id, count(tweets_id)as times_liked, tweets.users_id as users_id  from tweets left join liked_tweets on tweets.id = liked_tweets.tweets_id join users on users.id = tweets.users_id where tweets.id in (select t.id from tweets as t where t.users_id in (select user_being_followed from followed_users where user_following = %(user_id)s) or t.users_id =  %(user_id)s)group by tweets.id order by tweets.created_at DESC; ' 
        all_tweets =  mysql.query_db(query,data)

        print('ALL TWEETS: -------------------------',all_tweets)
       
       
       
       
       
       
        mysql = connectToMySQL('dojo_tweets')
        query = "SELECT * FROM liked_tweets WHERE users_id = %(user_id)s"
       
        liked_tweets = [tweet['tweets_id'] for tweet in mysql.query_db(query, data)]
        print('liked',liked_tweets)
       
       
        for tweet in all_tweets:
            time_since_posted = datetime.datetime.now() - tweet['time_posted']
            days = time_since_posted.days
            hours = time_since_posted.seconds//3600 
            minutes = (time_since_posted.seconds//60)%60
            if days < 0 :
                tweet['time_posted'] = (0, 0, 0)
            tweet['time_posted'] = (days, hours, minutes)
            print(tweet['time_posted'])
            if tweet['tweet_id'] in liked_tweets:
                tweet['already_liked'] = True
            else:
                tweet['already_liked'] = False
        
        print(all_tweets)
        
        return render_template('dashboard.html', user = user,tweets =all_tweets) 
    else:
        return redirect('/')
   
@app.route('/users')
def get_users():
    mysql = connectToMySQL('dojo_tweets')
    data = {
        'users_id': session['userid']
    }
    query = "SELECT * FROM users where users.id != %(users_id)s"
    followed_query = 'select  user_being_followed as following_user from followed_users  join users on followed_users.user_following = users.id where users.id = %(users_id)s;'

    users = mysql.query_db(query,data)
    mysql = connectToMySQL('dojo_tweets')
    users_followed = [user['following_user'] for user in mysql.query_db(followed_query,data)]
    print(users_followed)
    if users_followed:
        for user in users:
            user['followed'] = False
            if user['id'] in users_followed:
                user['followed']= True
    print(users)
    return render_template('users.html', users = users)

@app.route('/follow/<user_id>')
def follow_user(user_id):
    mysql = connectToMySQL('dojo_tweets')
    print('User',user_id)
    data = {
        'user_following': session['userid'],
        'user_being_follow': user_id
    }

    query = "insert into followed_users (user_following, user_being_followed) values ( %(user_following)s, %(user_being_follow)s);"
    

    
    users = mysql.query_db(query,data)
    return redirect('/users')

@app.route('/unfollow/<user_id>')
def unfollow_user(user_id):
    mysql = connectToMySQL('dojo_tweets')
    print('User',user_id)
    data = {
        'user_following': session['userid'],
        'user_being_follow': user_id
    }

    query = "delete from followed_users where user_following = %(user_following)s and  user_being_followed = %(user_being_follow)s;"
    mysql.query_db(query,data)
    return redirect('/users')

@app.route('/logout')
def logout_user():
    session.clear()
    return redirect('/')

@app.route('/tweet/create', methods = ['POST'])
def create_tweet():
    isValid = True

    if len(request.form['tweet']) < 1 or len(request.form['tweet']) > 255:
        isValid = False
        flash('Tweets must be between 1 and 255 characters long!','tweet_error') 
    print('before valid')
    print(isValid)
    if isValid:
        print('valid')
        data = {
            'tweet': request.form['tweet'],
            'user_id': session['userid'],
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }
        print(data)
        mysql = connectToMySQL("dojo_tweets")
        query = 'insert into tweets (content,created_at, updated_at, users_id) values (%(tweet)s,%(created_at)s,%(updated_at)s,%(user_id)s);'
        result = mysql.query_db(query,data)
        print(result)
    return redirect('/dashboard')

@app.route('/tweet/like/<tweet_id>', methods = ['GET'])
def like_tweet(tweet_id):
    print(tweet_id)
    mysql = connectToMySQL("dojo_tweets")
    data ={
        'user_id': session['userid'],
        'tweet_id': tweet_id
    } 
    query = 'insert into liked_tweets (users_id, tweets_id) values (%(user_id)s,%(tweet_id)s);'
    result = mysql.query_db(query,data)
    return redirect('/dashboard')

@app.route('/tweet/unlike/<tweet_id>')
def unlike_tweet(tweet_id):
    print(tweet_id)
    mysql = connectToMySQL("dojo_tweets")
    data ={
        'user_id': session['userid'],
        'tweet_id': tweet_id
    } 
    query = 'delete from liked_tweets where  users_id = %(user_id)s and tweets_id=%(tweet_id)s;'
    result = mysql.query_db(query,data)
    print(result)
    return redirect('/dashboard')

@app.route('/tweet/delete/<tweet_id>')
def delete_tweet(tweet_id):
    print(tweet_id)
    mysql = connectToMySQL("dojo_tweets")
    data ={
        'tweet_id': tweet_id
    } 
    query = 'delete from tweets where tweets.id =%(tweet_id)s;'
    delete_liked_tweet = 'delete from liked_tweets where tweets_id=%(tweet_id)s;'
    mysql.query_db(delete_liked_tweet,data)
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query,data)
    return redirect('/dashboard')



if __name__== "__main__":
    app.run(debug=True)