function show_comments(comments_button) {
    let comments = document.getElementById('comments')
    let history = document.getElementById('history')
    let history_button = document.getElementById('history_button')
    comments_button.style.color = '#fff'
    comments_button.style.backgroundColor = '#6c757d'
    history_button.style.color = ''
    history_button.style.backgroundColor = ''

    comments.style.display = ""
    history.style.display = "none"
}

function show_history(history_button) {
    console.log('history')
    let comments = document.getElementById('comments')
    let history = document.getElementById('history')
    let comments_button = document.getElementById('comments_button')
    comments_button.style.color = ''
    comments_button.style.backgroundColor = ''
    history_button.style.color = '#fff'
    history_button.style.backgroundColor = '#6c757d'

    comments.style.display = "none"
    history.style.display = ""
}


function delete_file(image_id) {
    $('#delete_file_' + image_id).modal('hide')
    $.ajax({
        type: 'POST',
        data: 'type=delete' + '&pk=' + image_id,
        success: function (response) {
            if (response.status === 'ok') {
                document.getElementById('file__' + image_id).remove()
            }
            else {
                alert('Что-то пошло не так, попробуйте снова')
            }
        },
        error: function () {
            alert('Что-то пошло не так, попробуйте снова')
        }
    })
}

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