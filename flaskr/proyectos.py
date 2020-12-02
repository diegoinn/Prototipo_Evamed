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
from shutil import copy

bp = Blueprint('proyectos', __name__)

def getFileName(idUsuario,idProject):

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


    return render_template('proyectos/proyectos.html',
                            Nombre = nombre,
                            Proyectos = proyectos,
                            NumProyectos = len(proyectos))


@bp.route('/proyecto/<int:idProyecto>')
@login_required
def proyecto(idProyecto):
    
    idUsuario = session.get('user_id')
    fileName = getFileName(idUsuario, idProyecto)
    
    db = get_db()

    proyecto = db.execute(
            'SELECT * FROM project WHERE idUser = ? and idProject = ?', (idUsuario,idProyecto)
        ).fetchone()

    proyectos = db.execute(
            'SELECT * FROM project WHERE idUser = ? and not idProject = ? order by fecha ASC', (idUsuario,idProyecto)
        ).fetchall()

    if not fileName:
        return redirect(url_for('index'))
    
    fileRoute = os.path.join(current_app.instance_path,fileName)
    if not(os.path.exists(fileRoute) and os.path.isfile(fileRoute)):
        return redirect(url_for('proyectos.configuraProyecto',idProyecto=idProyecto))

    return render_template('proyectos/analisis.html',proyecto = proyecto,proyectos=proyectos )


@bp.route('/creaProyecto',methods=['POST'])
@login_required
def creaProyecto():
    idUsuario = session.get('user_id')

    Nombre = request.form['nombre_proyecto'].strip()
    descripcion = request.form['descripcion_proyecto']
    clonar = request.form['clonar']

    db = get_db()
    cur = db.cursor()
    cur.execute(
        'INSERT INTO project (idUser, name, description, fecha) VALUES (?, ?, ?, ?)',
        (idUsuario, Nombre, descripcion, datetime.today())
    )
    db.commit()
    idClonar = -1
    try:
        idClonar = int(clonar)
    except:
        idClonar=-1

    idProyecto = cur.lastrowid
    if idClonar>=0:
        filenameClonar = getFileName(idUsuario,idClonar)
        fpc = os.path.join(current_app.instance_path,filenameClonar)
        
        fnO = getFileName(idUsuario,idProyecto)

        if filenameClonar and os.path.exists(fpc) and os.path.isfile(fpc) and fnO:
            fpo = os.path.join(current_app.instance_path,fnO)
            try:
                copy(fpc,fpo)
            except:
                pass

    
    return redirect(url_for('proyectos.configuraProyecto',idProyecto=idProyecto))



@bp.route('/getAnalisis/<int:idProyecto>')
@login_required
def getAnalisis(idProyecto):
    idUsuario = session.get('user_id')
    filename = getFileName(idUsuario,  idProyecto)
    
    db = get_db()

    proyecto = db.execute(
            'SELECT * FROM project WHERE idUser = ? and idProject = ?', (idUsuario,idProyecto)
        ).fetchone()
    if filename == False:
        return 'false'

    fileRoute = os.path.join(current_app.instance_path,filename)
    if not (os.path.exists(fileRoute) and os.path.isfile(fileRoute)):
        return 'false'
    
    instance_path = current_app.instance_path
    fr = os.path.join(instance_path,filename)
    with open(fr,'r') as f:
        info = json.load(f)

    fr = os.path.join(instance_path,'Impactos.csv')
    impactos = pd.read_csv(fr)

    fr = os.path.join(instance_path,'Transportes.csv')
    transporte = pd.read_csv(fr)

    impactos.loc[impactos['Abreviación'].isna(),'Abreviación'] = impactos.loc[impactos['Abreviación'].isna(),'Categoría de impacto']

    impactos['Indicador'] = impactos['Abreviación']
    impactos['Valor'] = impactos['A1-A3']


    transporte.loc[transporte['Abreviación'].isna(),'Abreviación'] = transporte.loc[transporte['Abreviación'].isna(),'Categoría de impacto']
    transporte['Indicador'] = transporte['Abreviación']

    impactoMateriales = None
    for material in info['Materiales']:
        if 'MaterialDB' in material.keys():
            impacto = impactos[impactos['Material'] == material['MaterialDB']]
            impacto.loc[:,'Valor'] = impacto['Valor'] * material['Cantidad']
            impacto = impacto[['Indicador','Valor']].set_index('Indicador')
            if impactoMateriales is None:
                impactoMateriales = impacto.fillna(0)
            else:
                impactoMateriales = impactoMateriales.add(impacto,fill_value=0).fillna(0)
        if 'Transporte' in material.keys():
            transporte['Valor'] = transporte[material['Transporte']] #* material['Distancia'] 
            transp = transporte[['Indicador','Valor']].set_index('Indicador')
            if impactoMateriales is None:
                impactoMateriales = transp.fillna(0)
            else:
                impactoMateriales = impactoMateriales.add(transp,fill_value=0).fillna(0)
        
    analisis = None
    if impactoMateriales is not None:
        impactoMateriales.reset_index(inplace=True)
        impactoMateriales['Etapa'] = 'Materiales'
        analisis = impactoMateriales[['Etapa','Indicador','Valor']].copy()


    fr = os.path.join(instance_path,'Construccion.csv')
    construccion = pd.read_csv(fr)

    construccion.loc[construccion['Abreviación'].isna(),'Abreviación'] = construccion.loc[construccion['Abreviación'].isna(),'Categoría de impacto']
    construccion['Indicador'] = construccion['Abreviación']


    impactos = None
    for m in info['Construccion']:
        construccion['Valor'] = construccion[m['maquina']] * m['horas'] 
        transp = construccion[['Indicador','Valor']].set_index('Indicador')
        if impactos is None:
            impactos = transp.fillna(0)
        else:
            impactos = impactos.add(transp,fill_value=0).fillna(0)

    if impactos is not None:
        impactos.reset_index(inplace=True)
        impactos['Etapa'] = 'Construcción'
        if analisis is None:
            analisis = impactos[['Etapa','Indicador','Valor']]
        else:
            analisis = analisis.append(impactos[['Etapa','Indicador','Valor']], ignore_index=True)

    fr = os.path.join(instance_path,'Uso.csv')
    uso = pd.read_csv(fr)

    uso.loc[uso['Abreviación'].isna(),'Abreviación'] = uso.loc[uso['Abreviación'].isna(),'Categoría de impacto']
    uso['Indicador'] = uso['Abreviación']

    impactos = None
    for m in info['Uso']:
        uso['Valor'] = uso[m['fuente']] * m['horas'] 
        transp = uso[['Indicador','Valor']].set_index('Indicador')
        if impactos is None:
            impactos = transp.fillna(0)
        else:
            impactos = impactos.add(transp,fill_value=0).fillna(0)

    if impactos is not None:
        impactos.reset_index(inplace=True)
        impactos['Etapa'] = 'Uso'
        if analisis is None:
            analisis = impactos[['Etapa','Indicador','Valor']]
        else:
            analisis = analisis.append(impactos[['Etapa','Indicador','Valor']], ignore_index=True)


    if analisis is not None:
        analisis['Porcentaje'] = 0
        indicadores = analisis.Indicador.unique()
        for indicador in indicadores:
            analisis.loc[analisis.Indicador == indicador,'Porcentaje'] = (analisis[analisis.Indicador == indicador].Valor * 100 / analisis[analisis.Indicador == indicador].Valor.sum())
        analisis = analisis[~analisis.Porcentaje.isna()]
        analisis['Poyecto'] = f'{proyecto["name"]}({proyecto["idProject"]})'
        analisis.loc[analisis.Indicador =='Human toxicity' ,'Indicador'] = 'HT'
        analisis.loc[analisis.Indicador =='Fresh water aquatic ecotox.' ,'Indicador'] = 'FWAE'
        analisis.loc[analisis.Indicador =='Marine aquatic ecotoxicity' ,'Indicador'] = 'MAE'
        analisis.loc[analisis.Indicador =='Terrestrial ecotoxicity' ,'Indicador'] = 'TE'
        return analisis.to_json(orient="records")
    return 'false'




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
    impactosConstruccion = pd.read_csv(os.path.join(current_app.instance_path,'Construccion.csv'))
    uso = pd.read_csv(os.path.join(current_app.instance_path,'Uso.csv'))

    titulos =['Categoría de impacto', 'Abreviación', 'Unidad']

    transportes = impactosTransportes.keys().tolist() 
    maquinas = impactosConstruccion.keys().tolist()
    energias = uso.keys().tolist()

    transportes = [ t for t in transportes if t not in titulos]
    maquinas = [ t for t in maquinas if t not in titulos]
    energias = [ t for t in energias if t not in titulos]


    unidades = materiales.Unidad.unique()

    session['idProyecto'] = idProyecto

    return render_template('proyectos/config.html',
                            proyecto=proyecto,unidades=unidades,
                            transportes=transportes,
                            materiales=materiales.to_dict(orient="records"),
                            maquinas = maquinas,
                            energias = energias)

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