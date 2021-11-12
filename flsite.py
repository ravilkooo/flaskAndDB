# pip install Flask
from flask import Flask, render_template, request, g, flash,\
    get_flashed_messages, abort, redirect, url_for, make_response
import sqlite3
import os
import time
from FDataBase import FDataBase
from UserLogin import UserLogin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm
from admin.admin import admin

# setting configurations
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'adadag4rij9h_w9hfh329q'
MAX_CONTENT_LENGTH = 1024*1024

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

app.register_blueprint(admin, url_prefix='/admin')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизируйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"


@login_manager.user_loader
def load_user(user_id):
    print("load_user()")
    return UserLogin().from_db(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    """Conn DB if not"""
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.before_request
def before_request():
    """Conn DB before req"""
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    """Disconnect DB"""
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route("/index")
@app.route("/")
def index():
    return render_template('index.html', menu=dbase.get_menu(), title='Главная',
                           posts=dbase.get_posts_announce())


@app.route("/add_post", methods=['POST', 'GET'])
def add_post():
    # Если данные пришли
    if request.method == 'POST':
        if len(request.form['title']) > 4 and len(request.form['text']) > 10 and len(request.form['url']) > 4:
            res = dbase.add_post(request.form['title'], request.form['text'], request.form['url'])
            if not res:
                flash('Ошибка добавления статьи', category='error')
            else:
                flash('Статья успешно добавлена', category='success')
        else:
            flash('Статья не подходит под минимальные требования', category='error')
    return render_template('add_post.html', menu=dbase.get_menu(), title='Добавить статью')


@app.route("/post/<alias>")
@login_required
def show_post(alias):
    title, text, tm = dbase.get_post(alias)
    if not title:
        abort(404)
    else:
        return render_template('post.html', title=title, text=text,
                               tm=tm, menu=dbase.get_menu(), ctime=time.ctime)


@app.route('/about')
def about():
    return render_template('about.html', title='О сайте', menu=dbase.get_menu())

# Старая версия
# @app.route('/login', methods=['POST', 'GET'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('profile'))
#
#     if request.method == 'POST':
#         user = dbase.get_user_by_email(request.form['email'])
#         if user and check_password_hash(user['psw'], request.form['psw']):
#             user_login = UserLogin().create(user)
#             rm = True if request.form.get('rememberme') else False
#             login_user(user_login, remember=rm)
#             # return redirect(url_for('profile'))
#             return redirect(request.args.get('next') or url_for('profile'))
#         flash("Неверный логин или пароль", "error")
#     return render_template('login.html', title='Авторизация', menu=dbase.get_menu())


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.get_user_by_email(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            user_login = UserLogin().create(user)
            rm = form.remember.data
            login_user(user_login, remember=rm)
            return redirect(request.args.get('next') or url_for('profile'))
        flash("Неверный логин или пароль", "error")
    return render_template("login.html", menu=dbase.get_menu(), title="Авторизация", form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hpsw = generate_password_hash(form.psw.data)
        res = dbase.add_user(form.name.data, form.email.data, hpsw)
        if res:
            flash("Вы успешно зарегестрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")

    return render_template('register.html', title='Регистрация', menu=dbase.get_menu(), form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html", menu=dbase.get_menu(), title="Профиль")


@app.route('/userava')
@login_required
def userava():
    img = current_user.get_avatar(app)
    if not img:
        return ""
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verify_ext(file.filename):
            try:
                img = file.read()
                res = dbase.update_user_avatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")
    return redirect(url_for('profile'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html', title='Страница не найдена', menu=dbase.get_menu())


if __name__ == '__main__':
    app.run(debug=True)


def just_method():
    print()
    return
