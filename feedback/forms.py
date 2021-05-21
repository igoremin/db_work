from django import forms
from .models import FeedBack


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedBack
        fields = ['name', 'text']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Введите отзыв',
                }
            ),
        }


class ChangeFeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedBack
        fields = ['answer', 'status']

        widgets = {
            'answer': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Введите ответ',
                }
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
