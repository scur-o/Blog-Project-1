from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from datetime import datetime, date
from flask_gravatar import Gravatar
import smtplib
import os

EMAIL = 'oscarinfoport@yahoo.com'
PASSWORD = 'xtsupkudbjfspdjb'

app = Flask(__name__)
Bootstrap(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# ------------------ CONNECT DB ------------------ #
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1', 'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ CONNECT LOGIN AUTH ------------------ #
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return NewUser.query.get(int(user_id))


# ------------------ TABLES CONFIG ------------------ #
class NewUser(UserMixin, db.Model):
    __tablename__ = 'new_users'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(250))
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comments', back_populates='comment_author')


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)

    author = relationship('NewUser', back_populates='posts')
    author_id = db.Column(db.String(250), db.ForeignKey('new_users.id'), nullable=False)

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship('Comments', back_populates='parent_post')


class Comments(UserMixin, db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('new_users.id'))
    comment_author = relationship('NewUser', back_populates='comments')
    parent_post = relationship('BlogPost', back_populates='comments')
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)


# db.create_all()


# ------------------ ROUTES ------------------ #
@app.route('/elements')
def elements():
    return render_template('elements.html', current_user=current_user)


# ------------------ LOG IN ROUTES ------------------ #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = NewUser.query.filter_by(email=email).first()
        if not user:
            flash('That email does not exist, please try again.')
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=8)
        if NewUser.query.filter_by(email=email).first():
            flash('Email already exists, try logging in instead.')
            return redirect(url_for('login'))
        else:
            new_user = NewUser(name=name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('register.html', current_user=current_user)


# ------------------ POSTS ------------------ #
@app.route('/', methods=['GET', 'POST'])
def home():
    all_posts = BlogPost.query.all()[::-1]
    if request.method == 'POST':
        name = request.form['name'],
        email = request.form['email'],
        message = request.form['message']
        send_email(name, email, message)
        flash('Message sent!')
        return redirect('#footer')
    return render_template('index.html', all_posts=all_posts, current_user=current_user)


@app.route('/post<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    current_post = BlogPost.query.get(post_id)
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('You need to login or register to comment.')
            return redirect(url_for('login'))
        new_comment = Comments(comment_author=current_user,
                               parent_post=current_post,
                               text=request.form['comment'],
                               date=date.today().strftime('%m-%d-%Y'),
                               )
        db.session.add(new_comment)
        db.session.commit()

    return render_template('post.html', post=current_post, current_user=current_user)


@app.route('/create-post', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        new_post = BlogPost(
            title=request.form['blog title'],
            subtitle=request.form['subtitle'],
            body=request.form['body'],
            img_url=request.form['img_url'],
            author=current_user,
            date=date.today().strftime('%B %d, %Y')
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create-post.html', current_user=current_user)


@app.route('/edit-post<int:post_id>')
def edit_post(post_id):
    current_post = BlogPost.query.get(post_id)
    return render_template('create-post.html', current_user=current_user)


@app.route('/about')
def about():
    return render_template('aboutme.html', current_user=current_user)


def send_email(name, email, message):
    email_message = f'Subject:Message from Blog\n\nName: {name}\nEmail: {email}\nMessage:{message}'
    with smtplib.SMTP('smtp.mail.yahoo.com', port=587) as connection:
        connection.starttls()
        connection.login(EMAIL, PASSWORD)
        connection.sendmail(EMAIL, 'osscaaryyip@gmail.com', email_message)



if __name__ == '__main__':
    app.run(debug=True)
