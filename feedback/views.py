from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from db_site.views import paginator_module
from .models import FeedBack, Profile
from .forms import FeedbackForm, ChangeFeedbackForm


def add_feedback(request):
    user = Profile.objects.get(user_id=request.user.id)
    if request.method == 'GET':
        form = FeedbackForm()
        context = {
            'form': form
        }
        return render(request, 'feedback/feedback_form.html', context=context)
    else:
        form = FeedbackForm(request.POST)
        if form.is_valid():
            new_feedback = form.save(commit=False)
            new_feedback.user = user
            form.save()
            return redirect(feedback_page, pk=new_feedback.pk)
        else:
            context = {
                'form': form
            }
            return render(request, 'feedback/feedback_form.html', context=context)


def feedback_list(request):
    if request.method == 'GET':
        if request.user.is_superuser:
            all_feedback = FeedBack.objects.all()
        else:
            all_feedback = FeedBack.objects.filter(user=Profile.objects.get(user_id=request.user.id))

        page, is_paginator, next_url, prev_url, last_url, paginator_dict = paginator_module(
            request=request, objects=all_feedback
        )

        context = {
            'all_feedback': all_feedback
        }
        context.update(paginator_dict)
        return render(request, 'feedback/feedback_list.html', context=context)


def feedback_page(request, pk):
    feedback = get_object_or_404(FeedBack, pk=pk)
    if request.user.is_superuser or feedback.user == Profile.objects.get(user_id=request.user.id):
        if request.method == 'GET':
            context = {
                'feedback': feedback
            }
            return render(request, 'feedback/feedback_page.html', context=context)
    else:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")


def change_feedback(request, pk):
    feedback = get_object_or_404(FeedBack, pk=pk)
    if request.user.is_superuser or feedback.user == Profile.objects.get(user_id=request.user.id):
        if request.method == 'GET':
            form = ChangeFeedbackForm(instance=feedback)
            context = {
                'form': form,
                'feedback': feedback,
            }
            return render(request, 'feedback/change_feedback_form.html', context=context)
        else:
            form = ChangeFeedbackForm(request.POST, instance=feedback)
            if form.is_valid():
                print('VALID')
                form.save()

            return redirect(feedback_page, pk=feedback.pk)
    else:
        return HttpResponseNotFound("У вас нет доступа к этой странице!")
