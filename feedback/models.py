from django.db import models
from django.utils import timezone
from django.shortcuts import reverse
from db_site.models import Profile
from django.utils.translation import gettext_lazy as _


class FeedBack(models.Model):
    class ChoicesStatus(models.TextChoices):
        OPEN = 'OPEN', _('Открыт')
        IN_WORK = 'WORK', _('В работе')
        DONE = 'DONE', _('Готов')
        CLOSE = 'CLOSE', _('Закрыт')

    user = models.ForeignKey(Profile, verbose_name='Пользователь', on_delete=models.PROTECT, blank=True, null=True)
    name = models.CharField(max_length=200, verbose_name='Тема')
    text = models.TextField(max_length=2000, verbose_name='Описание')
    answer = models.TextField(max_length=2000, verbose_name='Ответ', blank=True)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=5,
        choices=ChoicesStatus.choices,
        default=ChoicesStatus.OPEN,
        verbose_name='Статус')

    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['-date']

    def __str__(self):
        return '{}, пользователь : {}'.format(self.name, self.user)

    def get_absolute_url(self):
        return reverse('feedback_url', kwargs={'pk': self.pk})
