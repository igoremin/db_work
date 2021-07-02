function addSimpleObjectAria() {
    let form_id = document.getElementsByClassName('form_div').length;    //id новой формы

    let old_value = document.getElementById('id_form-TOTAL_FORMS').value;
    document.getElementById('id_form-TOTAL_FORMS').value =  Number(old_value) + 1;
    let place = document.getElementById('create_div');
    let select_form = document.getElementById('id_form-0-simple_object').cloneNode(true);
    let clone_form = document.getElementById('simple_object').cloneNode(true);
    // let clone_form = document.querySelectorAll('div.dropdown')[0].cloneNode(true);

    place.insertAdjacentElement('beforeEnd', clone_form);


    $('div.form_div div.dropdown:last').remove();

    $('div.form_div:last .col:first').append(select_form);

    let all_object_forms = document.getElementsByName('form-0-simple_object');
    let new_object_form = all_object_forms[all_object_forms.length - 1];
    new_object_form.name = 'form-' + form_id + '-simple_object';
    new_object_form.id = 'id_form-' + form_id + '-simple_object';
    new_object_form.selectedIndex = 0;

    let all_amount_forms = document.getElementsByName('form-0-amount');
    let new_amount_form = all_amount_forms[all_amount_forms.length - 1];
    new_amount_form.name = 'form-' + form_id + '-amount';
    new_amount_form.id = 'id_form-' + form_id + '-amount';
    new_amount_form.value = 0;

    let all_forms_amount = document.getElementsByClassName('form_div').length;

    $('.selectpicker').selectpicker();

    $.ajax({
        type: 'POST',
        data: "big_object_number_of_elements=" + all_forms_amount,
        error: function () {
            alert("Что-то пошло не так, попробуйте снова!");
            // $('#loader').hide();
        },
        success: function (data) {
            if (data.rez) {
                console.log(data.rez)
            }
            else {
                alert("Ошибка при проверке данных на сервере!\nПопробуйте снова.");
            }
        }
    })
}


$('#load_new_db_form').submit(function(e){
    console.log('CLICK');
    e.preventDefault();
    $form = $(this);
    let formData = new FormData(this);
    $('#loader').show();
    $.ajax({
        url: window.location.pathname,
        type: 'POST',
        data: formData,
        success: function (response) {
            $('#loader').hide();
            $('.error').remove();
            console.log(response);
            if(response.error){
                if(response.error_message) {
                    alert(response.error_message);
                }
                else {
                    $.each(response.errors, function(name, error){
                        error = '<small class="text-muted error">' + error + '</small>';
                        $form.find('[name=' + name + ']').after(error);
                    })
                }

            }
            else{
                alert(response.message);
                window.location = ""
            }
        },
        cache: false,
        contentType: false,
        processData: false
    });
});

$('#make_backup').submit(function (e){
    console.log('START BACKUP');
    e.preventDefault();
    $form = $(this);
    let formData = new FormData(this);
    $('#loader').show();
    $.ajax({
        url: this.action,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        cache: false,
        success: function (response) {
            $('#loader').hide();
            alert(response.rez);
        },
        error: function () {
            $('#loader').hide();
            alert("Что-то пошло не так, попробуйте снова!");
        }
    })
})



function createFile() {
    console.log('Create new file');
    $.ajax({
        type: 'POST',
        data: "action=create_new_file",
        error: function () {
            alert("Что-то пошло не так, попробуйте снова!");
            // $('#loader').hide();
        },
        success: function (data) {
            if (data.rez) {
                console.log(data.rez);
                location.reload();
                return false;
            }
            else {
                alert("Ошибка при проверке данных на сервере!\nПопробуйте снова.");
            }
        }
    })
}

$(function () {
    let tables = document.querySelectorAll('table.table');
    for (let table = 0; table < tables.length; table++) {
        let tds = tables[table].querySelectorAll('tbody tr td:first-child');

        for (let i = 0; i < tds.length; i++) {
            tds[i].innerHTML = i + 1;
        }
    }
});

function showTable() {
    let table = document.getElementById('big_objects_table');
    let button = document.getElementById('big_objects_button');
    if (table.style.display === "none") {
        table.style.display = "";
        button.value = 'Скрыть';
    }
    else {
        table.style.display = "none";
        button.value = 'Показать';
    }
}

function showCategory(object) {
    let files = document.getElementById('files_' + object.id);
    if (files.style.display === 'none') {
        files.style.display = ''
    }
    else {
        files.style.display = 'none'
    }
}

function showTableOnBigObjectPage(button) {
    console.log(button);
    let table = document.getElementById(button.id + '_table');
    if (table.style.display === 'none') {
        table.style.display = ''
    }
    else {
        table.style.display = 'none'
    }
}


$(function() {
  $('.selectpicker').selectpicker();
});

jQuery.fn.toggleOption = function( show ) {
    jQuery( this ).toggle( show );
    if( show ) {
        if( jQuery( this ).parent( 'span.toggleOption' ).length )
            jQuery( this ).unwrap( );
    } else {
        if( jQuery( this ).parent( 'span.toggleOption' ).length == 0 )
            jQuery( this ).wrap( '<span class="toggleOption" style="display: none;" />' );
    }
};

function check_categories_for_lab (lab) {
    let lab_txt = document.getElementById("select_current_lab").options[lab.val()].text;
    for (let current_cat = 1; current_cat < document.querySelectorAll("select#category_for_lab option").length; current_cat++) {
        let current_text = document.querySelectorAll("select#category_for_lab option")[current_cat].text
        if (current_text.indexOf(lab_txt) === -1) {
            jQuery(document.querySelectorAll("select#category_for_lab option")[current_cat]).toggleOption(false); // hide option
        }
        else {
            jQuery(document.querySelectorAll("select#category_for_lab option")[current_cat]).toggleOption(true); // show option
        }
    }
}

// $(window).load(function(){
$(document).ready(function() {
    var suggest_count = 0;
    var input_initial_value = '';
    var suggest_selected = 0;

    if (window.location.href.match('/search/') != null) {
        let search_word = $("#search_word")[0].innerHTML;
        console.log(search_word);
        let instance = new Mark(document.querySelectorAll("table"));
        instance.mark(search_word);
    }

    //Подключение скрипта для множественного выбора кабинета при загрузке страницы редактирования либо дававления нового простого объекта
    if ((window.location.href.match('objects/\.+/update') != null) || (window.location.href.match('objects/add') != null)) {
        $('#id_room').multiselect({
            buttonText: function(options, select) {
                if (options.length === 0) {
                    return 'Не выбран';
                }
                else if (options.length > 6) {
                    return 'Больше шести';
                }
                 else {
                     var labels = [];
                     options.each(function() {
                         if ($(this).attr('label') !== undefined) {
                             labels.push($(this).attr('label'));
                         }
                         else {
                             labels.push($(this).html());
                         }
                     });
                     return labels.join(', ') + '';
                 }
            }
        });
    }
    //При редактировании страницы отображаем только те категории которые доступны для выбранной лаботатории
    if (window.location.href.match('objects/\.+/update') != null) {
        let lab = $("#select_current_lab")
        check_categories_for_lab(lab)
        lab.change(function () {
            check_categories_for_lab(lab)
        })
    }
    //При создании нового объекта так же отображаем необходымые категории, при этом автоматом выставляем необходимую лабораторию
    //Подключаем  поиск уже существующих простых объектов при вводе нового названия
    if (window.location.href.match('objects/add') != null) {
        let lab_name = document.getElementById('lab_name');
        let lab = document.getElementById('select_current_lab');
        for (let l = 1; l < lab.length; l++) {
            if (lab.options[l].innerHTML === lab_name.innerHTML) {
                lab.options[l].selected = true;
                break;
            }
        }

        lab = $("#select_current_lab")
        check_categories_for_lab(lab);
        lab.change(function () {
            check_categories_for_lab(lab)
        })

        // читаем ввод с клавиатуры
        $("#search_box").keyup(function(I){
            // определяем какие действия нужно делать при нажатии на клавиатуру
            switch(I.keyCode) {
                // игнорируем нажатия на эти клавишы
                case 13:  // enter
                case 27:  // escape
                case 38:  // стрелка вверх
                case 40:  // стрелка вниз
                case 37:  // стрелка влево
                case 39:  // стрелка вправо
                    break;

                default:
                    // производим поиск только при вводе более 2х символов
                    if($(this).val().length>2){

                        input_initial_value = $(this).val();
                        $.ajax({
                            url: window.location.pathname,
                            type: 'GET',
                            data: 'q=' + input_initial_value,
                            error: function () {
                                alert('ERROR')
                            },
                            success: function (data) {
                                var list = eval("("+data.rez+")");
                                suggest_count = list.length;
                                if(suggest_count >= 0){
                                    // перед показом слоя подсказки, его обнуляем
                                    $("#search_advice_wrapper").html("").show();
                                    $('#search_advice_wrapper').append('Похожие варианты :');
                                    for(var i in list){
                                        if(list[i] != ''){
                                            // добавляем слою позиции
                                            $('#search_advice_wrapper').append('<div class="advice_variant">'+list[i]+'</div>');
                                        }
                                    }
                                }
                            }
                        });
                    }
                    else {
                        $("#search_advice_wrapper").html("").show();
                    }
                    break;
            }
        });

        //считываем нажатие клавишь, уже после вывода подсказки
        $("#search_box").keydown(function(I){
            switch(I.keyCode) {
                // по нажатию клавишь прячем подсказку
                case 13: // enter
                case 27: // escape
                    $('#search_advice_wrapper').hide();
                    return false;
                    break;
                // делаем переход по подсказке стрелочками клавиатуры
                case 38: // стрелка вверх
                case 40: // стрелка вниз
                    I.preventDefault();
                    if(suggest_count){
                        //делаем выделение пунктов в слое, переход по стрелочкам
                        key_activate( I.keyCode-39 );
                    }
                    break;
            }
        });

        // делаем обработку клика по подсказке
        $(document).on('click', '.advice_variant', function(){
            // ставим текст в input поиска
            $('#search_box').val($(this).text());
            // прячем слой подсказки
            $('#search_advice_wrapper').fadeOut(350).html('');
        });

        // если кликаем в любом месте сайта, нужно спрятать подсказку
        $('html').click(function(){
            $('#search_advice_wrapper').hide();
        });
        // если кликаем на поле input и есть пункты подсказки, то показываем скрытый слой
        $('#search_box').click(function(event){
            //alert(suggest_count);
            if(suggest_count)
                $('#search_advice_wrapper').show();
            event.stopPropagation();
        });
    }
    function key_activate(n){
        $('#search_advice_wrapper div').eq(suggest_selected-1).removeClass('active');

        if(n == 1 && suggest_selected < suggest_count){
            suggest_selected++;
        }else if(n == -1 && suggest_selected > 0){
            suggest_selected--;
        }

        if( suggest_selected > 0){
            $('#search_advice_wrapper div').eq(suggest_selected-1).addClass('active');
            $("#search_box").val( $('#search_advice_wrapper div').eq(suggest_selected-1).text() );
        } else {
            $("#search_box").val( input_initial_value );
        }
    }
});


$(function () {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
});
