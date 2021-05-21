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
