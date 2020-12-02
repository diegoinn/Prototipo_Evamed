
let datos = [];
let construccion=[];
let uso = [];

let SeleccionEC = null;
let SeleccionSC = null;
let SeleccionMaterial = null;
let maquinaTemplate = null;
let energiaTemplate = null;
$(document).ready(function () {
    //inicializa js de Materialize
    $('.tabs').tabs();
    $('.tooltipped').tooltip();

    maquinaTemplate = $($('.maquina')[0]).clone()
    energiaTemplate = $($('.energia')[0]).clone()

    $('select').formSelect({ dropdownOptions: { container: document.body } });


    // $('#ConfiguraMateriales').show();
    // $('#edicionMaterial').show();
    // $('#SeleccionMaterial').hide();
    // $('#CargarArchivo').hide();

    $('.busqueda-material').click(selecionaMaterialDB);
    $('#buscaMaterial').keyup(buscaMaterial);
    $('.SoloNumeros').keyup(soloNumeros);

    $('#CancelaeMaterial').click(cancelarMaterial);
    $('#GuardaMaterial').click(guardarMaterial);
    $('#ConfiguraMateriales').hide();
    $('#edicionMaterial').hide();
    $('#SeleccionMaterial').show(); 
    $('#SubirArchivo').click(leeArchivo)
    $('#ContConfigExistente').hide()

    $('#GuardarProyecto').click(guardarEnBase)
    
    $('#agregaMaquina').click(agregaMaquina)
    $('#agregaEnergia').click(agregaEnergia)

    getConfigExistente();
});

function agregaMaquina(){
    let nueva = maquinaTemplate.clone()
    $("#ContAgregaMaquina").before(nueva);
    $('select').formSelect({ dropdownOptions: { container: document.body } });
}

function agregaEnergia(){
    let nueva = energiaTemplate.clone()
    $("#ContAgregaEnergia").before(nueva);
    $('select').formSelect({ dropdownOptions: { container: document.body } });
}

function cargaDatosUso(){
    if (uso.length == 0){
        return;
    }
    $('.energia').remove();
    uso.forEach(element => {
        let nueva = energiaTemplate.clone()
        nueva.find('.fuente').val(element.fuente)
        nueva.find('.Horas').val(element.horas)
        $("#ContAgregaEnergia").before(nueva);
    });
    $('select').formSelect({ dropdownOptions: { container: document.body } });
}

function cargaDatosConstruccion(){
    if (construccion.length == 0){
        return;
    }
    $('.maquina').remove();
    construccion.forEach(element => {
        let nueva = maquinaTemplate.clone()
        nueva.find('.maquinaria').val(element.maquina)
        nueva.find('.Horas').val(element.horas)
        $("#ContAgregaMaquina").before(nueva);
    });
    $('select').formSelect({ dropdownOptions: { container: document.body } });

}

function guardaConstruccion(){
    construccion = []
    $('.maquina').each(function(){
        maquina = $(this);

        maquinaria = maquina.find('.maquinaria').val()
        horas =  maquina.find('.Horas').val()
        horasF = 0;
        try{
            horasF = parseFloat(horas);
        }catch{
            horasF=0;
        }
        if (maquinaria==null || maquinaria.trim() == '' ){

            return;
        }
        if(horasF == 0 || Number.isNaN(horasF)){
            return;
        }
        construccion.push({'maquina':maquinaria, 'horas':horasF});
    });
}


function guardaUso(){
    uso = []
    $('.energia').each(function(){
        energia = $(this);

        fuente = energia.find('.fuente').val()
        horas =  energia.find('.Horas').val()
        horasF = 0;
        try{
            horasF = parseFloat(horas);
        }catch{
            horasF=0;
        }
        if (fuente==null ||fuente.trim() == ''){

            return;
        }
        if(horasF == 0 || Number.isNaN(horasF)){
            return;
        }
        uso.push({'fuente':fuente, 'horas':horasF});
    });
}

function getConfigExistente(){
    
    $.ajax({
        url: '/getConfig',
		type:'GET',
        success: function(msj){
            let resultado = false;
            try{
                resultado = JSON.parse(msj)
            }catch{
                resultado = false
            }

            if (resultado == false){
                return;
            }

            datos = resultado.Materiales
            construccion = resultado.Construccion
            uso = resultado.Uso
            $('#ContConfigExistente').show()
            $('#ConfigExistente').click(cargaDatosMateriales)

        },
		error:function(msg){
			console.log('Error1',msg)
		}
    });
}


function guardarEnBase(){
    console.log('Guardando Configuración')

    guardaConstruccion();
    guardaUso();

    if(datos.length==0 && construccion.length==0 && uso.length==0){
        M.toast({html: 'Configurar el proyecto antes de Guardar'});
        return;
    }

    let infoProyecto = {'Materiales':datos,'Construccion':construccion,'Uso':uso};

    $.ajax({
        url: '/guardarConfig',
		type:'POST',
		contentType: 'application/json',
        data: JSON.stringify(infoProyecto),
        success: function(msj){
            let resultado = false;
            try{
                resultado = JSON.parse(msj)
            }catch{
                resultado = false
            }

            if (resultado){
                M.toast({html: 'Configuración Gardada'});
            }else{
                M.toast({html: 'Error guardando proyecto'});
                console.log(msj)
            }
        },
		error:function(msg){
			console.log('Error1',msg)
		}
    });



}

function soloNumeros(){
    let valor = $(this).val();
    valor = valor.replace(/[^0-9\.]/g,'').trim();
    $(this).val(valor);
}

function buscaMaterial() {
    let valor = $(this).val().trim()

    // console.log(valor)
    if (valor == '') {
        $('.busqueda-material').show()
        return;
    }


    $('.busqueda-material').each((index,material) => {
        let nombre = $(material).find('.nombre-material').text().trim()
        // console.log(nombre)
        if (nombre.toUpperCase().includes(valor.toUpperCase())) {
            $(material).show()
        } else {
            $(material).hide()
        }
    })

}

function selecionaMaterialDB() {
    let material = $(this).find('.nombre-material').text().trim();
    $('#MaterialDB').text(material);
    $('#buscaMaterial').val('');
    $('.busqueda-material').show();

}

function guardarMaterial() {
    let cantidad = $('#CantidadMaterial').val();
    let unidad = $('#UnidadMaterial').val();
    let tipoTrasporte = $('#TipoTransporte').val();
    let distanciaTransporte = $('#DistanciaTransporte').val()
    let materialDB = $('#MaterialDB').text();

    datos.forEach(element=>{
        if(SeleccionEC != 'TODOS' && SeleccionEC != element['Elemento Constructivo']){
            return;
        }
        if(SeleccionSC != 'TODOS' && SeleccionSC != element['Sistema Constructivo']){
            return;
        }
        if( SeleccionMaterial != element['Material']){
            return;
        }

        if(SeleccionEC != 'TODOS' && SeleccionSC != 'TODOS'){
            element.Cantidad = cantidad;
            element.Unidad = unidad;
        }

        distanciaTransporteF = 0

        try{
            distanciaTransporteF = parseFloat(distanciaTransporte)
        }catch{
            distanciaTransporteF=0;
        }
        
        element['Transporte'] = tipoTrasporte;
        element['Distancia'] = distanciaTransporteF;
        element['MaterialDB'] = materialDB;
    });

    guardarEnBase();

}

function cancelarMaterial() {
    SeleccionMaterial = null;

    $('#edicionMaterial').hide();
    $('#SeleccionMaterial').show();
}

function seleccionaMaterial(e) {
    let material = $(this).find('td').text().trim();
    let datosF = datos;
    SeleccionMaterial = material

    $('#edicionMaterial').show();
    $('#SeleccionMaterial').hide();

    $('#NombreMaterial').text(SeleccionMaterial);
    $('#SCMaterial').text(SeleccionSC);
    $('#ECMaterial').text(SeleccionEC);

    if(SeleccionEC == 'TODOS' || SeleccionSC == 'TODOS'){
        $('#DivCantidad').hide();
    }else{
        $('#DivCantidad').show();
    }


    if (SeleccionEC != 'TODOS') {
        datosF = datos.filter(element => { return element['Elemento Constructivo'].trim() == SeleccionEC })
    }

    if (SeleccionSC != 'TODOS') {
        datosF = datosF.filter(element => { return element['Sistema Constructivo'].trim() == SeleccionSC })
    }

    datosF = datosF.filter(element => { return element['Material'].trim() == SeleccionMaterial })

    if( datosF.length == 1){
        $('#CantidadMaterial').val(datosF[0].Cantidad);
        $('#UnidadMaterial').val(datosF[0].Unidad)
    }


    transportes = [...new Set(datosF.map(item => item['Transporte']))];
    transportes = transportes[0] == undefined ? [] : transportes;

    if ( transportes.length == 1 ){
        $('#TipoTransporte').val(transportes[0]);
    }else{
        $('#TipoTransporte').val('');
    }

    distancias = [...new Set(datosF.map(item => item['Distancia']))];
    distancias = distancias[0] == undefined ? [] : distancias;

    if (  distancias.length == 1 ){
        $('#DistanciaTransporte').val(distancias[0]);
    }else{
        $('#DistanciaTransporte').val('');
    }

    materialesDB = [...new Set(datosF.map(item => item['MaterialDB']))];
    materialesDB = materialesDB[0] == undefined ? [] : materialesDB;

    if (materialesDB.length == 1 ){
        $('#MaterialDB').text(materialesDB[0]);
    }else{

        $('#MaterialDB').text('---');
    }

    $('select').formSelect({ dropdownOptions: { container: document.body } });
}


function selecionaEC(e) {
    let EC = $(this).find('td').text().trim();
    let SCs = null;
    let datosF = datos;

    cancelarMaterial();

    $('#ElementosConst').find('tr').css('background-color', '');
    $(this).css('background-color', '#ccc');

    $('#SistemasConst').find('tr').css('background-color', '');

    $('#Materiales').find('tr').hide()

    // SeleccionEC = null;
    SeleccionEC = EC;
    if (EC != 'TODOS') {
        datosF = datos.filter(element => { return element['Elemento Constructivo'].trim() == EC })
    }

    SCs = ['TODOS', ...new Set(datosF.map(item => item['Sistema Constructivo'].trim()))];

    $('#SistemasConst').find('tr').each(function () {
        let tr = $(this)
        let dato = tr.find("td").text().trim()
        tr.hide();

        if (SCs.includes(dato)) {
            tr.show();
        }
    });
}

function seleccionaSC(e) {
    let SC = $(this).find('td').text().trim();
    let materiales = null;
    let datosF = datos;

    cancelarMaterial();

    $('#SistemasConst').find('tr').css('background-color', '');
    $(this).css('background-color', '#ccc');


    // SeleccionSC = null;
    if (SeleccionEC == null) {
        return;
    }
    SeleccionSC = SC;

    if (SeleccionEC != 'TODOS') {
        datosF = datos.filter(element => { return element['Elemento Constructivo'].trim() == SeleccionEC })
    }

    if (SC != 'TODOS') {
        datosF = datosF.filter(element => { return element['Sistema Constructivo'].trim() == SC })
    }

    materiales = [...new Set(datosF.map(item => item['Material'].trim()))];


    $('#Materiales').find('tr').each(function () {
        let tr = $(this)
        let dato = tr.find("td").text().trim()
        tr.hide();

        if (materiales.includes(dato)) {
            tr.show();
        }
    });


}


function cargaDatosMateriales() {
    cargaDatosConstruccion();
    cargaDatosUso();
    const EC = [...new Set(datos.map(item => item['Elemento Constructivo']))];
    const SC = [...new Set(datos.map(item => item['Sistema Constructivo']))];
    const material = [...new Set(datos.map(item => item['Material']))];

    $('#CargarArchivo').hide();
    $('#ConfiguraMateriales').show();

    EC.forEach(element => {
        elementoConstructivo = $(`
            <tr>
                <td class='EC'>
                    ${element.trim()}
                </td>
            </tr>
        `);

        $('#ElementosConst').append(elementoConstructivo)
    });
    $('#ElementosConst').find('tr').click(selecionaEC);


    SC.forEach(element => {
        sistemaConstructivo = $(`
            <tr>
                <td>
                    ${element.trim()}
                </td>
            </tr>
        `);

        $('#SistemasConst').append(sistemaConstructivo)
    });
    $('#SistemasConst').find('tr').hide()
    $('#SistemasConst').find('tr').click(seleccionaSC);

    material.forEach(element => {
        materialEL = $(`
            <tr>
                <td>
                    ${element.trim()}
                </td>
            </tr>
        `);
        $('#Materiales').append(materialEL)

    });
    $('#Materiales').find('tr').hide()
    $('#Materiales').find('tr').click(seleccionaMaterial);

}


function leeArchivo() {
    console.log('Inicializar archivo')
    var data = new FormData();
    archivo = $('#Archivo')[0].files[0];

    // if (archivo == undefined){
    //     M.toast({html: 'Seleccionar un archivo'});
    //     return;
    // } 

    data.append('file', archivo);
    $.ajax({
        url: '/parseFile',
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        method: 'POST',
        success: function (data) {
            let resultado;
            try {
                resultado = JSON.parse(data);
            } catch {
                resultado = false;
            }

            if (resultado != undefined && resultado != false) {
                datos = resultado;
                construccion = [];
                uso = [];
                cargaDatosMateriales();
            } else {
                M.toast({ html: 'Error al leer archivo' });
                return;
            }

        }
    });
}