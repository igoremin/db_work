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