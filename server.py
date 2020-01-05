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


@app.route("/get_sign_up", methods = ['GET'])
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


@app.route('/dashboard',methods =['GET'])
def get_dashboard():
    if 'userid' in session:
       return render_template('dashboard.html') 
    else:
        return redirect('/')
   


@app.route('/logout', methods=["GET"])
def logout_user():
    session.clear()
    return redirect('/')



if __name__== "__main__":
    app.run(debug=True)