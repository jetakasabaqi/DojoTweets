from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt 
import re
app = Flask(__name__)
app.secret_key='secret'
bcrypt = Bcrypt(app) 
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')  
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{5,}$')
@app.route("/")
def index():
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
                return redirect('dashboard.html')
        flash("Could not login", 'login_error')
    return redirect('/')


@app.route("/get_sign_up", methods = ['GET'])
def load_sign_up():
    return render_template('sign_up.html')





if __name__== "__main__":
    app.run(debug=True)