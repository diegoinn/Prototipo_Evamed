from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session, current_app
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db
import sys
import json
from datetime import datetime
import os
import pandas as pd
import json


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
    session.pop('idProyecto', None)

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

@bp.route('/proyecto/<int:idProyecto>')
@login_required
def proyecto(idProyecto):
    
    idUsuario = session.get('user_id')
    fileName = getFileName(idUsuario, idProyecto)
    if not fileName:
        return redirect(url_for('index'))
    
    fileRoute = os.path.join(current_app.instance_path,fileName)
    if not(os.path.exists(fileRoute) and os.path.isfile(fileRoute)):
        return redirect(url_for('proyectos.configuraProyecto',idProyecto=idProyecto))

    return f'{fileName}'





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
    
    
    materiales = pd.read_csv(os.path.join(current_app.instance_path,'Materiales.csv'))
    impactosTransportes = pd.read_csv(os.path.join(current_app.instance_path,'Transportes.csv'))

    titulos =['Categoría de impacto', 'Abreviación', 'Unidad']

    transportes = impactosTransportes.keys().tolist() 

    transportes = [ t for t in transportes if t not in titulos]
    unidades = materiales.Unidad.unique()

    session['idProyecto'] = idProyecto

    return render_template('proyectos/config.html',
                            proyecto=proyecto,unidades=unidades,
                            transportes=transportes,
                            materiales=materiales.to_dict(orient="records"))

@bp.route('/getConfig',methods=['GET'])
@login_required
def getConfig():
    idUsuario = session.get('user_id')
    idProject = session.get('idProyecto')

    nombreArchivo = getFileName(idUsuario,idProject)

    if nombreArchivo is False:
        return 'false'
    
    fp = os.path.join(current_app.instance_path ,nombreArchivo)

    if not os.path.isfile(fp):
        return 'false'
    
    datos = 'false'
    with open(fp,'r') as f:
        datos = f.read()

    return datos

@bp.route('/guardarConfig',methods=['POST'])
@login_required
def guardarConfig():
    idUsuario = session.get('user_id')
    idProject = session.get('idProyecto')

    nombreArchivo = getFileName(idUsuario,idProject)

    if nombreArchivo is False:
        return 'false'

    datos = request.get_json(force=True,silent=True)
    if datos is None:
        return 'false'

    fp = os.path.join(current_app.instance_path,nombreArchivo)
    with open(fp,'w') as f:
        json.dump(datos,f)
    
    return json.dumps(True)


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),'Temp',)
ALLOWED_EXTENSIONS = {'xlsx'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/parseFile',methods=['POST'])
@login_required
def parseFile():
    if 'file' not in request.files:
        return 'false'
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return 'false'

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        # return 'archivo guardado'
        
        base=pd.read_excel(os.path.join(UPLOAD_FOLDER, filename),sheet_name=None)

        base_total = None

        for k in base.keys():
            if base[k].shape[0]>0:
                base[k].drop('Fuente de información', axis=1, inplace=True)
                base[k]['Elemento Constructivo'] = k
                if base_total is None:
                    base_total = base[k].copy()
                else:
                    base_total = base_total.append(base[k], ignore_index=True)

        base_total.loc[base_total.Unidad == 'm2','Unidad'] = 'm²'
        base_total.loc[base_total.Unidad == 'm3','Unidad'] = 'm³'
        base_total.loc[base_total.Unidad == 'pzas','Unidad'] = 'Pza'
        response = base_total.to_json(orient="records")

        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                os.remove(os.path.join(root, file))
        return response