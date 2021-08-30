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


function addNewSimpleObject() {
    let form = $('#base_form')
    let table = document.getElementById('all_components_table')
    $.ajax({
        type: 'POST',
        data: 'form=' + form.serialize(),
        url: form.attr('action'),
        error: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else{
                alert("Что-то пошло не так, попробуйте снова!");
            }
        },
        success: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else if (data.rez) {
                if (data.new_page_url) {
                    window.history.pushState({"html":data.new_html,"pageTitle": 'TEST'},"", data.new_page_url);
                }
                let new_html = new DOMParser().parseFromString(data.new_html, 'text/html');
                let new_table = new_html.getElementById('all_components_table');
                let new_base_form = new_html.getElementById('base_form')
                console.log(new_base_form)
                let delete_modal = new_html.getElementById('delete_' + data.pk);
                table.replaceWith(new_table);
                form.replaceWith(new_base_form)
                $('.selectpicker').selectpicker();
                $('#main_div').append(delete_modal);
                tableRowsNumber();
            }
            else {
                alert("Ошибка при проверке данных на сервере!\nПопробуйте снова.");
            }
        }
    })
}

function deleteComponentFromBigObject(pk) {
    console.log(pk);
    $.ajax({
        type: 'POST',
        data: 'delete=' + pk,
        error: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else{
                alert("Что-то пошло не так, попробуйте снова!");
            }
        },
        success: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else if (data.not_found) {
                console.log(data.not_found);
            }
            else if (data.rez) {
                console.log(data.rez);
                $('#delete_' + pk).modal('toggle')
                $('#tr_' + pk).remove()

                tableRowsNumber()
            }
            else {
                alert("Ошибка при проверке данных на сервере!\nПопробуйте снова.");
            }
        }
    })
}

function updateComponentFromBigObject(pk) {
    let new_amount = document.getElementsByName('new_amount_' + pk)[0]
    $.ajax({
        type: 'POST',
        data: 'update=' + pk + "&new_amount=" + new_amount.value,
        error: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else{
                alert("Что-то пошло не так, попробуйте снова!");
            }
        },
        success: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else if (data.not_found) {
                console.log(data.not_found);
            }
            else if (data.rez) {
                console.log(data.rez);
                $('#change_' + pk).modal('toggle')
                let pos = 5;
                if (data.pos) {
                    pos = 4;
                }
                $('tr#tr_' + pk + ' td:nth-child(' + pos +')').text(data.new_amount.toFixed(1));
            }
            else {
                alert("Ошибка при проверке данных на сервере!\nПопробуйте снова.");
            }
        }
    })
}

function add_new_comment() {
    let form = $('#comment_form')
    console.log(form.serialize());
    let files = $('#id_file');
    // let files_data = new FormData($('#id_file')[0].files);
    // console.log(files_data)
    // files_data.append('file', files)
    // console.log(files);
    $.ajax({
        type: 'POST',
        data: 'file=' + files.prop("files"),
        enctype: 'multipart/form-data',
        // contentType: 'application/json',
        // processData: false,
        error: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else{
                alert("Что-то пошло не так, попробуйте снова!");
            }
        },
        success: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else if (data.rez) {
                console.log(data.rez);
                let new_html = new DOMParser().parseFromString(data.new_html, 'text/html');
                let new_comments = new_html.getElementById('comments');
                let old_comments = document.getElementById('comments')
                old_comments.replaceWith(new_comments)
                simplemde.value('')
            }
        }
    })
}

function change_task_status(type) {
    $.ajax({
        url: window.location.pathname + 'change_status/',
        type: 'POST',
        data: 'type=' + type,
        error: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else{
                alert("Что-то пошло не так, попробуйте снова!");
            }
        },
        success: function (data) {
            if (data.err) {
                alert(data.err);
            }
            else if (data.rez) {
                location.reload();
                return false;
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

function tableRowsNumber () {
    let tables = document.querySelectorAll('table.table');
    for (let table = 0; table < tables.length; table++) {
        let tds = tables[table].querySelectorAll('tbody tr td:first-child');

        for (let i = 0; i < tds.length; i++) {
            tds[i].innerHTML = i + 1;
        }
    }
}

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

function showTableOnPage(button) {
    console.log(button);
    let table = document.getElementById(button.id + '_table');
    if (table.style.display === 'none') {
        table.style.display = ''
    }
    else {
        table.style.display = 'none'
    }
}

function CatTypeSelectChange(select) {
    //Функция для отображения и скрытия выбора типа объекта в том случае если это поле не используется
    let p_obj_type = select.parentElement.nextElementSibling;
    if (select.value === 'SO') {
        p_obj_type.style.display = '';
    }
    else {
        p_obj_type.style.display = 'none';
        let obj_type = p_obj_type.lastChild
        for (let l = 0; l < obj_type.length; l++) {
            if (obj_type.options[l].value === 'DF') {
                obj_type.options[l].selected = true;
                break;
            }
        }
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

$(document).ready(function () {
    // $('.treetable').treetable();
    if (window.location.href.match('/create_new_task/') != null || window.location.href.match('/update_task/') != null || window.location.href.match('/tracker/\.+/all/\.+') != null) {
        $('#id_executors').multiselect({
            buttonText: function(options, select) {
                if (options.length === 0) {
                    return 'Не выбраны';
                }
                else if (options.length > 3) {
                    return 'Больше трех';
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
    console.log(window.location.href);
    if (window.location.href.match('tracker/.+/all/.*/?$') != null || window.location.href.match('worker/.+/$') != null) {
        var
            $table = $('table.tree-table'),
            rows = $table.find('tr');

        rows.each(function (index, row) {
            var
                $row = $(row),
                level = $row.data('level'),
                id = $row.data('id'),
                $columnName = $row.find('td[data-column="name"]'),
                children = $table.find('tr[data-parent="' + id + '"]');

            // if (children.length) {
            //     var expander = $columnName;
            //
            //     children.hide();
            //
            //     expander.on('click', function (e) {
            //         var $target = $(e.target);
            //         if ($target.hasClass('glyphicon-chevron-right')) {
            //             console.log('IF')
            //             $target
            //                 .removeClass('glyphicon-chevron-right')
            //                 .addClass('glyphicon-chevron-down');
            //
            //             children.show();
            //         } else {
            //             console.log('ELSE')
            //             $target
            //                 .removeClass('glyphicon-chevron-down')
            //                 .addClass('glyphicon-chevron-right');
            //
            //             reverseHide($table, $row);
            //         }
            //     });
            // }
            //width:' + 15 * level + 'px;
            let r = ''
            for (let i = 1; i < level; i++) {
                r = r + '---'
            }
            $columnName.prepend('' +
                '<span class="treegrid-indent" style="display:inline-block">' + r + '</span>');
        });

        // Reverse hide all elements
        // reverseHide = function (table, element) {
        //     var
        //         $element = $(element),
        //         id = $element.data('id'),
        //         children = table.find('tr[data-parent="' + id + '"]');
        //
        //     if (children.length) {
        //         children.each(function (i, e) {
        //             reverseHide(table, e);
        //         });
        //
        //         $element
        //             .find('.glyphicon-chevron-down')
        //             .removeClass('glyphicon-chevron-down')
        //             .addClass('glyphicon-chevron-right');
        //
        //         children.hide();
        //     }
        // };

    }
})

$(document).ready(function() {
    if (window.location.href.match('sort=') != null) {
        let select = document.getElementById('select_sorted');
        let old_prefix = $('#old_sorted_prefix').val().split('=')[1];

        for (let l = 1; l < select.length; l++) {
            if (select.options[l].value === old_prefix) {
                select.options[l].selected = true;
                break;
            }
        }

    }
})

// $(window).load(function(){
$(document).ready(function() {
    var suggest_count = 0;
    var input_initial_value = '';
    var suggest_selected = 0;

    tableRowsNumber()

    if (window.location.href.match('/search/') != null) {
        let search_word = $("#search_word")[0].innerHTML;
        console.log(search_word);
        let instance = new Mark(document.querySelectorAll("table"));
        instance.mark(search_word);
    }

    //Подключение скрипта для множественного выбора кабинета при загрузке страницы редактирования либо дававления нового простого объекта
    if ((window.location.href.match('objects/\.+/update') != null) || (window.location.href.match('objects/add') != null) || (window.location.href.match('create_simple') != null) || window.location.href.match('create_new_simple_object') != null) {
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
    if (window.location.href.match('objects/\.+/update') != null || window.location.href.match('create_simple') != null ) {
        let lab = $("#select_current_lab")
        check_categories_for_lab(lab)
        lab.change(function () {
            check_categories_for_lab(lab)
        })
    }
    //При создании нового объекта так же отображаем необходымые категории, при этом автоматом выставляем необходимую лабораторию
    //Подключаем  поиск уже существующих простых объектов при вводе нового названия
    if (
        window.location.href.match('objects/add') != null ||
        window.location.href.match('create_new_simple_object') != null ||
        window.location.href.match('create_new_base_object') != null
    ) {
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
