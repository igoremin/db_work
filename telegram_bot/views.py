import telebot
import threading
from threading import Thread
from telebot import types, apihelper
from db_site.models import LabName, Profile
from tracker.models import Task, CommentForTask
from django.core.exceptions import ObjectDoesNotExist
from django.utils.formats import date_format
from django.conf import settings
from db_site.views import home_page
from django.shortcuts import redirect
from html.parser import HTMLParser

if not settings.DEBUG:
    apihelper.proxy = {'https': 'http://serv.sao.ru:8080'}

bot = telebot.TeleBot(settings.TELEGRAM_KEY)


class StringParser(HTMLParser):
    def __init__(self, text):
        self.support_tags = {
            'b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'a', 'code', 'pre'
        }
        self.text = text
        super(StringParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        if tag not in self.support_tags:
            image_url = None

            if tag == 'img':
                for attr in attrs:
                    if attr[0] == 'src':
                        image_url = attr[1]
            if attrs:
                remove_str = f'<{tag}'
                for attr in attrs:
                    remove_str += f' {attr[0]}="{attr[1]}"'
                remove_str += ' />'
                if image_url:
                    self.text = self.text.replace(remove_str, image_url)
                else:
                    self.text = self.text.replace(remove_str, '')
            else:
                self.text = self.text.replace(f'<{tag}>', '')

    def handle_endtag(self, tag):
        if tag not in self.support_tags:
            self.text = self.text.replace(f'</{tag}>', '')


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


def format_text_to_tg_html_style(text):
    parser = StringParser(text=text)
    parser.feed(text)
    return parser.text


def menu(message, task=None, call=False):
    if call:
        chat_id = message.message.chat.id
    else:
        chat_id = message.chat.id

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    if task:
        key_read_comments = types.InlineKeyboardButton(
            text='Посмотреть комментарии', callback_data=f'read_comments_for_task__{task.pk}'
        )
        key_add_comment = types.InlineKeyboardButton(
            text='Добавить комментарий', callback_data=f'add_comment_for_task__{task.pk}'
        )
        keyboard.add(key_read_comments, key_add_comment)
    key_task_list = types.InlineKeyboardButton(
        text='Все задачи', callback_data='tasks_list'
    )
    key_my_tasks = types.InlineKeyboardButton(
        text='Мои задачи', callback_data='tasks_list__for_user'
    )
    keyboard.add(key_task_list, key_my_tasks)

    profile = Profile.objects.get(tg_id=message.from_user.id)
    if profile.user.is_superuser:
        key_change_lab = types.InlineKeyboardButton(text='Сменить лабораторию', callback_data='change_lab')
        keyboard.add(key_change_lab)

    bot.send_message(
        chat_id,
        text=f'Меню',
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@bot.message_handler(commands=['start', 'help'])
def start_message(message, call=False):
    if not call:
        if not check_user(message):
            bot.reply_to(message, not_found_user_message(message))
            return
    profile = Profile.objects.get(tg_id=message.from_user.id)

    lab = profile.tg_current_lab
    if profile.tg_current_lab is None:
        Profile.objects.filter(tg_id=message.from_user.id).update(tg_current_lab=profile.lab)
        lab = profile.lab

    if call:
        chat_id = message.message.chat.id
        message_id = message.message.message_id - 1
        message = message.message
    else:
        chat_id = message.chat.id
        message_id = message.message_id - 1
    try:
        bot.edit_message_reply_markup(
            chat_id,
            message_id=message_id,
        )
    except:
        pass

    bot.send_message(
        chat_id,
        text=f'Добрый день!\nТекущая лаборатория : {lab.name}',
        reply_markup=types.ReplyKeyboardRemove()
    )

    menu(message)


def run():
    bot.polling(none_stop=True)


@bot.callback_query_handler(func=lambda call: 'tasks_list' in call.data)
def tasks_for_lab(message):
    """Список задач для конкретной лаборатории"""
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    profile = Profile.objects.get(tg_id=message.from_user.id)
    if message.data == 'tasks_list':
        all_tasks = Task.objects.filter(lab=profile.tg_current_lab)
    else:
        all_tasks = Task.objects.filter(executors__exact=profile)
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
        bot.delete_message(chat_id=message.message.chat.id, message_id=message.message.message_id)
        bot.send_message(
            chat_id=message.message.chat.id,
            text=f'Задачи для лаборатории "{profile.tg_current_lab.name}" не найдены!',
        )
        bot.answer_callback_query(callback_query_id=message.id, text='')
        start_message(message, call=True)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def task_info(message):
    """Информация по выбранной задаче"""
    if not check_user(message):
        bot.reply_to(message, not_found_user_message(message))
        return
    try:
        task = Task.objects.get(id=message.text.split(',')[-1].split(':')[-1].strip())
        profile = Profile.objects.get(tg_id=message.from_user.id)
        text = f'<strong>Название задачи</strong> : {task.name}\n' \
               f'<strong>Описание</strong> : {task.get_message_as_markdown().replace("<p>", "").replace("</p>", "")}\n' \
               f'<strong>Статус</strong> : {task.get_status_display()}'
        if task.create_date:
            text += f'\n<strong>Дата создания</strong> : {date_format(task.create_date)}'
        if task.start_date:
            text += f'\n<strong>К задаче приступили</strong> : {date_format(task.start_date)}'
        if task.end_date:
            text += f'\n<strong>Дедлайн</strong> : {date_format(task.end_date)}'
        if profile in task.new_comment_for_executors.all():
            text += '\n<strong>В данной задаче есть новые комментарии!</strong>&#128276'
        if len(text) > 4096:
            for x in range(0, len(text), 4096):
                bot.send_message(
                    message.chat.id,
                    text=text[x:x + 4096],
                    parse_mode='HTML',
                    reply_markup=types.ReplyKeyboardRemove(),
                )
        else:
            bot.send_message(
                message.chat.id,
                text=text,
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove(),
            )
        menu(message, task)
    except ValueError:
        start_message(message)


@bot.callback_query_handler(func=lambda call: 'read_comments_for_task__' in call.data)
def read_task_comments(call):
    """Вовыод комментариев для конкретной задачи"""
    if not check_user(call):
        bot.reply_to(call, not_found_user_message(call))
        return
    profile = Profile.objects.get(tg_id=call.from_user.id)
    task = Task.objects.get(id=call.data.split('__')[-1].strip())
    comments = CommentForTask.objects.filter(task=task)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.send_message(call.message.chat.id, text='Комментарии для задачи')

    for comment in comments:
        text = ''
        name = comment.user.name
        if comment.user.robot:
            name += ' <i>(робот)</i>'
        text += f'<strong>Автор</strong> : {name}\n'
        text += f'<strong>Дата</strong> : {date_format(comment.date)}\n'
        text += format_text_to_tg_html_style(comment.get_message_as_markdown())
        if len(text) > 4096:
            for x in range(0, len(text), 4096):
                bot.send_message(
                    call.message.chat.id,
                    text=text[x:x + 4096],
                    parse_mode='HTML'
                )
        else:
            bot.send_message(
                call.message.chat.id,
                text=text,
                parse_mode='HTML'
            )
    if profile in task.new_comment_for_executors.all():
        task.new_comment_for_executors.remove(profile)
    menu(call, task, call=True)


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
    menu(message, task)


@bot.callback_query_handler(func=lambda call: call.data == 'change_lab')
def callback_inline__change_lab(call):
    user = True
    if user:
        # markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        all_labs = LabName.objects.all()
        if len(all_labs) > 0:
            for lab in all_labs:
                key_select_lab = types.InlineKeyboardButton(text=lab.name, callback_data=f'new_lab__{lab.slug}')
                keyboard.add(key_select_lab)
                # markup.add(types.KeyboardButton(text=lab))
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Выберите лабораторию',
                reply_markup=keyboard,
            )
            # bot.register_next_step_handler(msg, change_lab)
            bot.answer_callback_query(callback_query_id=call.id, text='')


@bot.callback_query_handler(func=lambda call: 'new_lab__' in call.data)
def change_lab(call):
    if not check_user(call):
        bot.reply_to(call, not_found_user_message(call))
        return
    new_lab = LabName.objects.get(slug=call.data.split('__')[-1])
    Profile.objects.filter(tg_id=call.from_user.id).update(tg_current_lab=new_lab)
    profile = Profile.objects.get(tg_id=call.from_user.id)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.send_message(
        chat_id=call.message.chat.id,
        text=f'Пользователь {profile.name}.\nЛаборатория для отображения в телеграм боте : {new_lab.name}',
    )
    bot.answer_callback_query(callback_query_id=call.id, text='')
    menu(call, call=True)


def start_bot(request):
    if request.user.is_superuser and request.method == 'GET':
        tg_bot = Thread(target=run)
        tg_bot.name = 'TG_bot'
        tg_bot.start()
    return redirect(home_page)


def stop_bot(request):
    if request.user.is_superuser and request.method == 'GET':
        print('STOP BOT')
        for thread in threading.enumerate():
            if thread.name == 'TG_bot':
                print(thread)
                bot.stop_polling()
    return redirect(home_page)
