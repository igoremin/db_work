from django.db import models
from db_site.models import BigObject, Profile, LabName, del_path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.shortcuts import reverse
from django.utils.html import mark_safe
from django.utils.formats import date_format
from markdown import markdown
from threading import Thread
import os


def generate_path_for_files(instance, filename):
    if instance.comment:
        return 'comments/{0}/{1}'.format(instance.comment.pk, filename)


def get_all_children_for_task(top_task, include_self=False, status=None):
    top_level = 1
    if status is None:
        status = ['IW', 'NW', 'CT', 'CF']

    all_children = []

    def get_children_for_task(task, level):
        children = Task.objects.filter(parent=task)
        for child in children:
            if child.status in status:
                all_children.append([child, level])

            if child.if_get_children():
                if child.status in status:
                    level += 1
                get_children_for_task(child, level)

    if include_self:
        if top_task.status in status:
            all_children.append([top_task, 1])
            top_level += 1

    if top_task.if_get_children():
        get_children_for_task(top_task, top_level)

    return all_children


class Task(models.Model):
    class ChoicesStatus(models.TextChoices):
        OPEN = 'NW', _('Не в работе')
        IN_WORK = 'IW', _('В работе')
        CLOSE_TRUE = 'CT', _('Закрыто (решен)')
        CLOSE_FALSE = 'CF', _('Закрыто (не решен)')

    parent = models.ForeignKey(to='self', verbose_name='Родитель', on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, verbose_name='Название')
    lab = models.ForeignKey(to=LabName, verbose_name='Лаборатория', on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField(verbose_name='Дата и время создания', editable=False)
    last_modified = models.DateTimeField(verbose_name='Дата и время последнего изменения', editable=False)
    start_date = models.DateTimeField(verbose_name='Дата начала', editable=False, blank=True, null=True)
    end_date = models.DateField(verbose_name='Дата окончания')
    close_date = models.DateTimeField(verbose_name='Дата закрытия задачи', editable=False, blank=True, null=True)
    text = models.TextField(verbose_name='Описание', blank=True, null=True)
    creator = models.ForeignKey(
        verbose_name='Создатель', to=Profile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='creator_task'
    )
    executors = models.ManyToManyField(
        verbose_name='Исполнители', to=Profile, blank=True,
        related_name='executors_task'
    )
    big_object = models.ForeignKey(
        to=BigObject, verbose_name='Объект', on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=2,
        choices=ChoicesStatus.choices,
        default=ChoicesStatus.OPEN,
        verbose_name='Статус'
    )
    new_comment_for_executors = models.ManyToManyField(
        verbose_name='Новые комментарии для исполнителей', to=Profile, blank=True,
        related_name='executors_task_new_message'
    )
    privat = models.BooleanField(verbose_name='Приватная задача', default=False, blank=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-create_date']

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.last_modified = timezone.now()
        if not self.id:
            self.create_date = timezone.now()
            if self.status == 'IW':
                self.start_date = timezone.now()
        else:
            old_self = Task.objects.get(pk=self.pk)
            if old_self.status == 'NW' and self.status == 'IW':
                self.start_date = timezone.now()
            if old_self.status == 'IW' and self.status in ['CT', 'CF']:
                self.close_date = timezone.now()
        super(Task, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('task_page_url', kwargs={'lab': self.lab.slug, 'pk': self.pk})

    def if_get_children(self):
        if Task.objects.filter(parent=self):
            return True
        return False

    def can_close(self):
        all_children = self.get_all_children()
        all_done_children = self.get_all_children(status=['CT', 'CF'])
        if all_children == all_done_children:
            return True
        return False

    def get_children(self):
        return Task.objects.filter(parent=self)

    def get_all_children(self, include_self=False, status=None):
        return get_all_children_for_task(self, include_self, status)

    def get_message_as_markdown(self):
        return mark_safe(markdown(self.text))

    def get_color(self):
        if self.status in ['NW', 'IW']:
            days_left = self.end_date - timezone.now().date()
            if days_left.days < 0:
                return '#ffa3a3'
            elif 0 <= days_left.days <= 3:
                return '#fff9a3'
            else:
                return '#a9ffa3'
        else:
            return None

    def add_new_comment(self, text, author):
        new_comment = CommentForTask()
        new_comment.text = text
        new_comment.task = self
        new_comment.user = author
        new_comment.save()
        self.new_comment_for_executors.set(self.executors.all())
        self.create_tg_message_text(comment=new_comment, author=author)
        return new_comment

    def create_tg_message_text(self, comment, author):
        message = f'В задаче <b>{self.name}</b> есть новое сообщение: \n'
        name = comment.user.name
        if comment.user.robot:
            name += ' <i>(робот)</i>'
        message += f'<strong>Автор</strong> : {name}\n'
        message += f'<strong>Дата</strong> : {date_format(comment.date)}\n'
        message += comment.get_message_as_markdown()
        Thread(target=self.send_message_in_tg, args=(message, author)).start()

    def send_message_in_tg(self, message, author=None):
        from telegram_bot.views import send_message
        users = self.executors.filter(tg_id__isnull=False, tg_chat_id__isnull=False)
        for user in users:
            if user != author:
                send_message(text=message, user=user)

    def add_robot_comment(self, text, author):
        self.new_comment_for_executors.set(self.executors.all())
        self.new_comment_for_executors.remove(author)
        robot = Profile.objects.filter(robot=True).order_by('?')[0]
        if robot:
            new_comment = CommentForTask(
                task=self,
                user=robot,
                text=text
            )
            new_comment.save()
            self.create_tg_message_text(comment=new_comment, author=author)

    @staticmethod
    def get_task_tree(lab, private=False, user=None):
        all_task = []
        all_done_task = []
        if private is True and user:
            top_task_for_lab = Task.objects.filter(lab__slug=lab, parent=None, privat=True, creator=user)
        else:
            top_task_for_lab = Task.objects.filter(lab__slug=lab, parent=None, privat=False)

        for task in top_task_for_lab:
            all_task.append(task.get_all_children(include_self=True, status=['NW', 'IW']))
            done_task = task.get_all_children(include_self=True, status=['CT', 'CF'])
            if len(done_task) > 0:
                all_done_task.append(done_task)
        return all_task, all_done_task


class CommentForTask(models.Model):
    task = models.ForeignKey(to=Task, on_delete=models.CASCADE, verbose_name='Комментарий к задаче',
                             related_name='comments')
    user = models.ForeignKey(to=Profile, on_delete=models.SET_NULL, null=True, verbose_name='Пользователь')
    date = models.DateTimeField(verbose_name='Дата и время комментария', editable=False)
    text = models.TextField(verbose_name='Текст комментария')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['date']

    def __str__(self):
        return f'{self.user.name}, {self.task.name}'

    def save(self, *args, **kwargs):
        if not self.id:
            self.date = timezone.now()
        super(CommentForTask, self).save(*args, **kwargs)

    def get_absolute_url_for_change(self):
        return reverse('change_comment_url', kwargs={'lab': self.task.lab.slug, 'task_pk': self.task.pk, 'pk': self.pk})

    def get_message_as_markdown(self):
        return mark_safe(markdown(self.text))


class FileForComment(models.Model):
    comment = models.ForeignKey(CommentForTask, on_delete=models.CASCADE, related_name='files', verbose_name='Файл')
    file = models.FileField(upload_to=generate_path_for_files, verbose_name='Файл', blank=True)

    class Meta:
        verbose_name = 'Файл к комментарию'
        verbose_name_plural = 'Файлы к комментариям'
        ordering = ['comment']

    def __str__(self):
        return f'Файл для : {self.comment}'

    def filename(self):
        return os.path.basename(self.file.name)

    def delete(self, *args, **kwargs):
        full_path = str(self.file.path).rsplit(os.sep, 1)[0]
        self.file.delete(save=False)
        del_path(full_path)
        super().delete(*args, **kwargs)
