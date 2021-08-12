from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from gevent.pywsgi import WSGIServer
import flask
import flask_login

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    detail = db.Column(db.String(100))
    due = db.Column(db.DateTime, nullable=False)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
app.secret_key = 'super secret string'
users = {'shinji@hoge': {'password': 'secret'}}

class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template('login.html')

    email = flask.request.form['email']
    if flask.request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return flask.redirect(flask.url_for('index'))

    #return 'Bad login'
    flash('Invalid username or password. Please try again!')
    return flask.redirect(flask.url_for('login'))

@app.route('/logout')
def logout():
    flask_login.logout_user()
    #return 'Logged out'
    return flask.redirect(flask.url_for('login'))

@login_manager.unauthorized_handler
#def unauthorized_handler():
def unauthorized():
    return flask.redirect('/login')

@app.route('/', methods=['GET','POST'])
@flask_login.login_required
def index():
    flash('Logged in as: ' + flask_login.current_user.id)
    if request.method == 'GET':
        posts = Post.query.order_by(Post.due).all()
        return render_template('index.html', posts=posts, today=date.today())
    else:
        title = request.form.get('title')
        detail = request.form.get('detail')
        due = request.form.get('due')

        due = datetime.strptime(due, '%Y-%m-%d')
        new_post = Post(title=title, detail=detail, due=due)

        db.session.add(new_post)
        db.session.commit()

        return redirect('/')

@app.route('/create')
@flask_login.login_required
def create():
    return render_template('create.html')

@app.route('/detail/<int:id>')
@flask_login.login_required
def read(id):
    post = Post.query.get(id)
    return render_template('detail.html', post=post)

@app.route('/update/<int:id>', methods=['GET','POST'])
@flask_login.login_required
def update(id):
    post = Post.query.get(id)
    if request.method == 'GET':
        return render_template('update.html', post=post)
    else:
        post.title = request.form.get('title')
        post.detail = request.form.get('detail')
        post.due = datetime.strptime(request.form.get('due'),'%Y-%m-%d')
        db.session.commit()
        return redirect('/')

@app.route('/delete/<int:id>')
@flask_login.login_required
def delete(id):
    post = Post.query.get(id)

    db.session.delete(post)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    #app.run(host="0.0.0.0",port=8000,debug=True)
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()

