from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
import sys
import json
from datetime import datetime
import os

bp = Blueprint('proyectos', __name__)

def getFileName(idUsuario,idProject):
    
    idUsuario = session.get('user_id')

    db = get_db()

    proyecto = db.execute(
            'SELECT * FROM project WHERE idUser = ? and idProject = ?', (idUsuario,idProject)
        ).fetchone()
    if proyecto is None:
        return False
    
    return f'{idUsuario}_{idProject}.json'

@bp.route('/')
@login_required
def index():
    nombre = session.get('user_fullName')
    idUsuario = session.get('user_id')
    db = get_db()
    proyectos = db.execute(
            'SELECT * FROM project WHERE idUser = ? order by fecha ASC', (idUsuario,)
        ).fetchall()
    print([elt['idProject'] for elt in proyectos])
    return render_template('proyectos/proyectos.html',
                            Nombre = nombre,
                            Proyectos = proyectos,
                            NumProyectos = len(proyectos))



@bp.route('/creaProyecto',methods=['POST'])
@login_required
def creaProyecto():
    idUsuario = session.get('user_id')

    Nombre = request.form['nombre_proyecto'].strip()
    descripcion = request.form['descripcion_proyecto']

    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO project (idUser, name, description, fecha) VALUES (?, ?, ?, ?)',
        (idUsuario, Nombre, descripcion, datetime.today())
    )
    db.commit()
    # session['proyect_id'] = cur.lastrowid
    # print(cur.lastrowid)
    # return(f'{cur.lastrowid}')
    return redirect(url_for('proyectos.configuraProyecto',idProyecto=cur.lastrowid))

@bp.route('/configuraProyecto/<int:idProyecto>')
@login_required
def configuraProyecto(idProyecto):
    
    idUsuario = session.get('user_id')

    db = get_db()

    proyecto = db.execute(
            'SELECT * FROM project WHERE idUser = ? and idProject = ?', (idUsuario,idProyecto)
        ).fetchone()
    if proyecto is None:
        return redirect(url_for('index'))
    
    return render_template('proyectos/config.html',proyecto=proyecto)

@bp.route('/proyecto/<int:idProyecto>')
@login_required
def proyecto(idProyecto):
    
    idUsuario = session.get('user_id')
    fileName = getFileName(idUsuario, idProyecto)
    if not fileName:
        return redirect(url_for('index'))
    
    fileRoute = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','instance',fileName)
    if not(os.path.exists(fileRoute) and os.path.isfile(fileRoute)):
        return redirect(url_for('proyectos.configuraProyecto',idProyecto=idProyecto))

    return f'{fileName}'