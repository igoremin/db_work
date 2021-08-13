from django import forms
from .models import Task, CommentForTask, FileForComment
from db_site.models import Profile, BigObject
from django.utils.translation import ugettext_lazy as _


class TaskForm(forms.ModelForm):
    parent_list = None
    executor_list = None
    big_objects_list = None

    class Meta:
        model = Task
        fields = ['executors', 'big_object', 'name', 'text', 'end_date', 'privat']

        widgets = {
            'executors': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'big_object': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'end_date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Дата'}),
            'privat': forms.CheckboxInput(attrs={'class': 'form-check-label'})
        }

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.executor_list = Profile.objects.filter(lab__slug=lab)
        self.big_objects_list = BigObject.objects.filter(base__lab__slug=lab, top_level=True)
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['executors'].queryset = self.executor_list
        self.fields['big_object'].queryset = self.big_objects_list
        if 'instance' in kwargs.keys():
            task = kwargs['instance']
            if task.get_children():
                self.fields['privat'].widget = forms.HiddenInput()


class TaskForTaskForm(forms.ModelForm):
    executor_list = None

    class Meta:
        model = Task
        fields = ['executors', 'name', 'text', 'end_date']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'id': 'new_task_for_task__text'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Дата'}),

        }

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        self.executor_list = Profile.objects.filter(lab__slug=lab)
        super(TaskForTaskForm, self).__init__(*args, **kwargs)
        self.fields['executors'].queryset = self.executor_list


class CommentForTaskForm(forms.ModelForm):
    class Meta:
        model = CommentForTask
        fields = ['text', ]

        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 1, 'cols': 2}),
        }


class FileForCommentForm(forms.ModelForm):
    class Meta:
        model = FileForComment
        fields = ['file', ]

        widgets = {
            'file': forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control-file', 'required': False}),
        }
        labels = {
            "file": _("Выберите файлы"),
        }
