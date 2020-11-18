import functools

from flaskr.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


# Middleware
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE idUser = ?', (user_id,)
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


# Routes
@bp.route('/logout')
def logout():
    session.clear()
    # Cambiar endpoint
    return redirect(url_for(''))


@bp.route('/register', methods=('GET', 'POST'))
def register():
    # Validate request
    if request.method == 'POST':
        # Fetch data
        fullName = request.form['fullName']
        email = request.form['email']
        enterprise = request.form['enterprise']
        password = request.form['password']
        privacy = request.form['privacy']
        db = get_db()
        error = None

        # Validate data
        if not fullName:
            error = 'Nombre completo requerido.'
        elif not email:
            error = 'Correo requerido.'
        elif not enterprise:
            error = 'Empresa o institución requerida.'
        elif not password:
            error = 'Contraseña requerida.'
        elif not privacy:
            error = 'Confirma términos y condiciones.'
        elif db.execute(
                'SELECT idUser FROM user WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = 'El correo {} ya está registrado.'.format(email)

        # Create user
        if error is None:
            db.execute(
                'INSERT INTO user (fullName, email, enterprise, password) VALUES (?, ?, ?, ?)',
                (fullName, email, enterprise, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    # Validate request
    if request.method == 'POST':
        # Fetch data
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE email = ?', (email,)
        ).fetchone()

        # Validate data
        if user is None or not check_password_hash(user['password'], password):
            error = 'Correo o contraseña incorrecta.'

        # Redirect
        if error is None:
            session.clear()
            session['user_id'] = user['idUser']
            session['user_fullName'] = user['fullName']
 
            # Cambiar endpoint
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')
