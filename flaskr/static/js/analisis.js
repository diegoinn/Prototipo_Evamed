
datos = {}
proyectoActual = null
chart = null
$(document).ready(function () {
    //inicializa j = s de Materialize
    $('select').formSelect({ dropdownOptions: { container: document.body } });
    
    getAnalisisProyecto($('#idProyecto').text(),v => {
        proyectoActual=v;
        creaGrafica();        
    });


    $('#Proyectos').change(agregaProyecto)
});

function agregaProyecto(){
    let id = $(this).val().toString()
    
    $(this).val('')

    $('select').formSelect({ dropdownOptions: { container: document.body } });

    getAnalisisProyecto(id,v =>{
        if (Object.keys(datos).includes(id)){
            delete datos[id]
        }else{
            datos[id] = v;
        }
        creaGrafica();        
    });
}

function getAnalisisProyecto(idProyecto, callback){

    $.ajax({
        url:'/getAnalisis/'+idProyecto,
        method: 'GET',
        success: function(msg){
            try{
                newProyect = JSON.parse(msg)
            }catch{
                newProyect = false
            }
            if( newProyect == false){
                M.toast({ html: 'Error al obtener Analisis' });
            }else{
                callback(newProyect)
            }
        }

    });


}

function creaGrafica(){
    let info = [...proyectoActual]
    let xs = ['Indicador']
    Object.keys(datos).forEach(k =>{
        info = [...info,...datos[k]]
        xs =['Indicador','Poyecto']
    });
    if (chart != null){
        console.log(chart)
        chart.destroy()
    }
    chart = new Taucharts.Chart({
        data: info,
        type: 'stacked-bar',           
        x: xs,
        y: 'Porcentaje',
        color: 'Etapa',
        plugins: [
            Taucharts.api.plugins.get('legend')(),
            Taucharts.api.plugins.get('tooltip')(),
        ]
    });
    $('#barchart').html('')
    chart.renderTo('#barchart')
}