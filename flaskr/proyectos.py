from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
import sys
import json

bp = Blueprint('proyectos', __name__)

@bp.route('/')
@login_required
def index():
    nombre = session.get('user_fullName')
    idUsuario = session.get('user_id')
    db = get_db()
    proyectos = db.execute(
            'SELECT * FROM project WHERE idUser = ?', (idUsuario,)
        ).fetchall()
    print(proyectos)
    return render_template('proyectos/proyectos.html',
                            Nombre = nombre,
                            Proyectos = json.dumps(proyectos),
                            NumProyectos = len(proyectos))
