import telebot
from telebot import types
from db_site.models import LabName, Profile
from tracker.models import Task, CommentForTask
from django.core.exceptions import ObjectDoesNotExist
from django.utils.formats import date_format
from django.conf import settings

bot = telebot.TeleBot(settings.TELEGRAM_KEY)


def check_user(message):
    user_id = message.from_user.id
    if user_id in Profile.objects.all().values_list('tg_id', flat=True):
        return True
    else:
        return False


def not_found_user_message(message):
    return f"Пользователь не найден.\n" \
           f"Для того чтобы получить доступ к возможностям телеграм бота необходимо в личном кабинете указать ID\n" \
           f"Ваш ID : {message.from_user.id}"


def menu_for_task(message, task):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    comments = CommentForTask.objects.filter(task=task)
    if len(comments) > 1:
        key_read_comments = types.InlineKeyboardButton(
            text='Посмотерть комментарии', callback_data=f'read_comments_for_task__{task.pk}'
        )
        keyboard.add(key_read_comments)
    key_add_comment = types.InlineKeyboardButton(
        text='Добавить комментарий', callback_data=f'add_comment_for_task__{task.pk}'
    )
    keyboard.add(key_add_comment)

    bot.send_message(
        message.chat.id,
        text=f'Меню для выбранной задачи',
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return

    profile = Profile.objects.get(tg_id=message.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    key_tasks = types.InlineKeyboardButton(text='Мои задачи', callback_data='tasks_list__for_user')
    key_all_tasks = types.InlineKeyboardButton(text='Все задачи для лаборатории', callback_data='tasks_list')
    if profile.user.is_superuser:
        key_change_lab = types.InlineKeyboardButton(text='Сменить лабораторию', callback_data='change_lab')
        keyboard.add(key_change_lab, key_tasks, key_all_tasks)
    else:
        keyboard.add(key_tasks, key_all_tasks)

    lab = profile.tg_current_lab
    if profile.tg_current_lab is None:
        Profile.objects.filter(tg_id=message.from_user.id).update(tg_current_lab=profile.lab.slug)
        lab = profile.lab.slug
    try:
        current_lab = LabName.objects.get(slug=lab)
    except ObjectDoesNotExist:
        current_lab = Profile.objects.get(tg_id=message.from_user.id).lab

    bot.send_message(
        message.chat.id,
        text=f'Главное меню\nТекущая лаборатория : {current_lab}',
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda message: True, content_types=['text'])
def change_lab(message):
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return
    new_lab = message.text
    Profile.objects.filter(tg_id=message.from_user.id).update(tg_current_lab=new_lab)
    profile = Profile.objects.get(tg_id=message.from_user.id)
    bot.send_message(
        chat_id=message.chat.id,
        text=f'Пользователь {profile.name}.\nЛаборатория для отображения в телеграм боте : {profile.tg_current_lab}',
        reply_markup=types.ReplyKeyboardRemove()
        )
    start_message(message)


@bot.callback_query_handler(func=lambda call: 'tasks_list' in call.data)
def tasks_for_lab(message):
    """Список задач для конкретной лаборатории"""
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    profile = Profile.objects.get(tg_id=message.from_user.id)
    if message.data == 'tasks_list':
        all_tasks = Task.objects.filter(lab__slug=profile.tg_current_lab)
    else:
        all_tasks = Task.objects.filter(lab__slug=profile.tg_current_lab, executors__exact=profile)
    if len(all_tasks) > 0:
        for task in all_tasks:
            if task.create_date:
                text = f'{task.name}, создана {date_format(task.create_date)}, id: {task.pk}'
            else:
                text = f'{task.name}'
            markup.add(types.KeyboardButton(text=text))
        bot.delete_message(chat_id=message.message.chat.id, message_id=message.message.message_id)
        msg = bot.send_message(
            chat_id=message.message.chat.id,
            text='Выберите задачу',
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, task_info)
        bot.answer_callback_query(callback_query_id=message.id, text='')
    else:
        bot.send_message(
            chat_id=message.message.chat.id,
            text='Ничего не найдено!',
        )
        start_message(message)


def task_info(message):
    """Информация по выбранной задаче"""
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return
    task = Task.objects.get(id=message.text.split(',')[-1].split(':')[-1].strip())
    text = f'Название задачи : {task.name}\n' \
           f'Описание : {task.text}\n' \
           f'Статус : {task.get_status_display()}'
    if task.create_date:
        text += f'\nДата создания : {date_format(task.create_date)}'
    if task.start_date:
        text += f'\nК задаче приступили : {date_format(task.start_date)}'
    if task.end_date:
        text += f'\nДедлайн : {date_format(task.end_date)}'
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=types.ReplyKeyboardRemove())
    menu_for_task(message, task)


@bot.callback_query_handler(func=lambda call: 'read_comments_for_task__' in call.data)
def read_task_comments(call):
    """Вовыод комментариев для конкретной задачи"""
    if not check_user(call):
        bot.reply_to(call, not_found_user_message(call))
        return
    task = Task.objects.get(id=call.data.split('__')[-1].strip())
    comments = CommentForTask.objects.filter(task=task)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    text = ''
    for comment in comments:
        name = comment.user.name
        if comment.user.robot:
            name += ' _(робот)_'
        text += f'*Автор* : {name}\n'
        text += f'*Дата* : {date_format(comment.date)}\n'
        text += f'*Текст* : {comment.text}\n----------------------\n'

    bot.send_message(call.message.chat.id, text='Комментарии для задачи')
    bot.send_message(
        call.message.chat.id,
        text=text.replace('**', '*'),
        parse_mode='Markdown'
    )
    menu_for_task(call.message, task)


@bot.callback_query_handler(func=lambda call: 'add_comment_for_task__' in call.data)
def add_comment_for_task(call):
    """Добавление нового комментария к задаче"""
    if not check_user(call):
        bot.reply_to(call, not_found_user_message(call))
        return
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    new_comment = bot.send_message(
        chat_id=call.message.chat.id,
        text='Введите комментарий для задачи',
    )
    task = Task.objects.get(id=call.data.split('__')[-1].strip())
    bot.register_next_step_handler(new_comment, save_new_comment_for_task, task.pk)
    bot.answer_callback_query(callback_query_id=call.id, text='')


def save_new_comment_for_task(message, task_pk):
    """Сохранение нового комментария для задачи"""
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return
    task = Task.objects.get(pk=task_pk)
    new_comment = CommentForTask()
    new_comment.text = message.text
    new_comment.task = task
    new_comment.user = Profile.objects.get(tg_id=message.from_user.id)
    new_comment.save()
    bot.send_message(
        chat_id=message.chat.id,
        text='Комментарий добавлен!',
    )
    menu_for_task(message, task)


@bot.callback_query_handler(func=lambda call: call.data == 'change_lab')
def callback_inline__change_lab(call):
    user = True
    if user:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        all_labs = LabName.objects.all().values_list('slug', flat=True)
        if len(all_labs) > 0:
            for lab in all_labs:
                markup.add(types.KeyboardButton(text=lab))
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            msg = bot.send_message(
                chat_id=call.message.chat.id,
                text='Выберите лабораторию',
                reply_markup=markup,
            )
            bot.register_next_step_handler(msg, change_lab)
            bot.answer_callback_query(callback_query_id=call.id, text='')
