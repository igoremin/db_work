from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from .models import Task, CommentForTask, FileForComment
from .forms import TaskForm, CommentForTaskForm, TaskForTaskForm, FileForCommentForm
from django.contrib.auth.decorators import login_required
from db_site.models import Profile, LabName
from django.utils import formats


@login_required(login_url='/login/')
def task_list(request, lab):
    user = get_object_or_404(Profile, user_id=request.user.id)
    if user.lab.slug != lab and request.user.is_superuser is False:
        raise Http404

    if request.method == 'GET':
        all_task, all_done_task = Task.get_task_tree(lab=lab)
        all_private_tasks, all_done_private_task = Task.get_task_tree(lab=lab, private=True, user=user)

        context = {
            'task_list': all_task,
            'done_task_list': all_done_task,
            'private_task_list': all_private_tasks,
            'done_private_task_list': all_done_private_task,
            'profile': user,
        }
        return render(request, 'tracker/task_list.html', context=context)


@login_required(login_url='/login/')
def task_page(request, lab, pk):
    user = get_object_or_404(Profile, user_id=request.user.id)
    if user.lab.slug != lab and request.user.is_superuser is False:
        raise Http404
    task = get_object_or_404(Task, lab__slug=lab, pk=pk)
    if request.method == 'GET':
        task.new_comment_for_executors.remove(user)
        task_tree = task.get_all_children(include_self=False, status=['IW', 'NW'])
        comments = CommentForTask.objects.filter(task=task, user__robot=False)
        history = CommentForTask.objects.filter(task=task, user__robot=True)
        new_comment_form = CommentForTaskForm()
        task_for_task_form = TaskForTaskForm(lab=lab)
        add_new_files_form = FileForCommentForm()
        user_can_change = False
        if user in task.executors.all() or user == task.creator or request.user.is_superuser:
            user_can_change = True
        context = {
            'task': task,
            'comments': comments,
            'history': history,
            'comment_form': new_comment_form,
            'task_for_task_form': task_for_task_form,
            'user_can_change': user_can_change,
            'task_tree': task_tree,
            'add_new_files_form': add_new_files_form,
        }
        return render(request, 'tracker/task_page.html', context)
    else:
        comment = False
        if request.POST.get('text'):
            form = CommentForTaskForm(request.POST)
            if form.is_valid():
                new_comment = form.save(commit=False)
                comment = task.add_new_comment(text=new_comment.text, author=user)
        if request.FILES:
            form = FileForCommentForm(request.POST, request.FILES)
            if form.is_valid() and comment:
                files = request.FILES.getlist('file')
                for file in files:
                    new_file = FileForComment(
                        file=file,
                        comment=comment
                    )
                    new_file.save()
        return redirect(task_page, lab, pk)


@login_required(login_url='/login/')
def change_comment(request, lab, task_pk, pk):
    task = get_object_or_404(Task, pk=task_pk)
    comment = get_object_or_404(CommentForTask, pk=pk)
    user = get_object_or_404(Profile, user_id=request.user.id)
    if user.lab.slug != lab and not (request.user.is_superuser or user == comment.user):
        raise Http404

    comment_form = CommentForTaskForm(instance=comment)
    files = comment.files.all()

    context = {
        'task': task,
        'comment': comment,
        'comment_form': comment_form,
        'files': files,
        'new_files_form': FileForCommentForm(),
    }
    if request.method == 'GET':
        return render(request, 'tracker/change_comment.html', context)
    elif request.method == 'POST' and request.is_ajax():
        request_dict = request.POST.dict()
        if request.POST.get('type') and request.POST.get('pk'):
            if request_dict['type'] == 'delete':
                try:
                    file = FileForComment.objects.get(pk=request_dict['pk'])
                    file.delete()
                    return JsonResponse({'status': 'ok'}, status=200)
                except ObjectDoesNotExist:
                    return JsonResponse({'status': 'file not found'}, status=200)
                except ValueError:
                    return JsonResponse({'status': 'expected a number'}, status=200)
        return JsonResponse({'status': 'false'}, status=200)
    elif request.method == 'POST':
        if request.POST.get('text'):
            form = CommentForTaskForm(request.POST)
            if form.is_valid():
                new_comment = form.save(commit=False)
                comment.text = new_comment.text
                comment.save()
            else:
                context['comment_form'] = form
                return render(request, 'tracker/change_comment.html', context)
        if request.FILES:
            form = FileForCommentForm(request.POST, request.FILES)
            if form.is_valid():
                files = request.FILES.getlist('file')
                for file in files:
                    new_file = FileForComment(
                        file=file,
                        comment=comment
                    )
                    new_file.save()
        return redirect(change_comment, lab, task_pk, pk)


@login_required(login_url='/login/')
def task_form(request, lab, pk=None):
    task = None
    user = get_object_or_404(Profile, user_id=request.user.id)
    if user.lab.slug != lab and not request.user.is_superuser:
        raise Http404

    if pk is not None:
        task = get_object_or_404(Task, lab__slug=lab, pk=pk)

    if request.method == 'GET':
        form = TaskForm(lab=lab)
        if pk is not None:
            form = TaskForm(instance=task, lab=lab)
        context = {
            'task': task,
            'form': form
        }
        return render(request, 'tracker/task_form.html', context)
    else:

        if pk is not None:
            name = task.name
            executors = set(task.executors.all())
            end_date = task.end_date
            text = task.text
            form = TaskForm(request.POST, instance=task, lab=lab)
            if form.is_valid():
                message = f'???????????????????????? {user.name} ????????(????) ?????????????????? : \n'
                bot_send = False
                form.save()
                if name != task.name:
                    message += f'-**???????????? ????????????????** : "{name}", **??????????** : "{task.name}"\n'
                    bot_send = True
                if executors != set(task.executors.all()):
                    bot_send = True
                    new_executors = set(task.executors.all())
                    if len(executors) == len(new_executors):
                        message += '-**???????????????? ?????????????????????? : **'
                    elif len(executors) < len(new_executors):
                        message += '-**?????????????????? ?????????????????????? : **'
                    else:
                        message += '-**???????????? ?????????????????????? : **'
                    ex = [executor.name for executor in (executors ^ new_executors)]
                    message += ', '.join(ex)
                    message += '\n'
                if end_date != task.end_date:
                    bot_send = True
                    end_date = formats.date_format(end_date, 'SHORT_DATE_FORMAT')
                    new_end_date = formats.date_format(task.end_date, 'SHORT_DATE_FORMAT')
                    message += f'-**?????????????? ?????????????????? ??** "{end_date}" **????** "{new_end_date}"\n'
                if text != task.text:
                    bot_send = True
                    message += f'-**???????????????? ???????????????????? : ** \n"{task.text}"'
                if bot_send:
                    task.add_robot_comment(message, user)
                return redirect(task_page, lab=lab, pk=pk)
            else:
                context = {
                    'form': form,
                    'task': task,
                }
                return render(request, 'tracker/task_form.html', context)
        else:
            form = TaskForm(request.POST, lab=lab)
            if form.is_valid():
                lab = get_object_or_404(LabName, slug=lab)

                new_task = form.save(commit=False)
                new_task.creator = user
                new_task.lab = lab
                new_task.save()

                new_task.executors.set(form.clean()['executors'])
                new_task.executors.add(user)

                text = f'{user.name} ????????????(a) ?????? ????????????'
                new_task.add_robot_comment(text, user)
                return redirect(task_page, lab=lab.slug, pk=new_task.pk)
            else:
                context = {
                    'form': form,
                    'task': task,
                }
                return render(request, 'tracker/task_form.html', context)


@login_required(login_url='/login/')
def create_task_for_exist_task(request, lab, pk):
    user = get_object_or_404(Profile, user_id=request.user.id)
    if user.lab.slug != lab and not request.user.is_superuser:
        raise Http404
    if request.method == 'POST':
        form = TaskForTaskForm(request.POST, lab=lab)
        if form.is_valid():
            parent = get_object_or_404(Task, pk=pk)
            lab = get_object_or_404(LabName, slug=lab)
            new_task = form.save(commit=False)
            new_task.parent = parent
            new_task.big_object = parent.big_object
            new_task.lab = lab
            new_task.creator = user
            new_task.privat = parent.privat
            new_task.save()

            parent.add_robot_comment(
                f'{user.name} ????????????(a) ?????????????????? "[{new_task.name}]'
                f'({new_task.get_absolute_url()})"', user
            )
            text = f'{user.name} ????????????(a) ?????? ?????????????????? ?????? ???????????? "{parent.name}"'
            new_task.add_robot_comment(text, user)
            return redirect(task_page, lab=lab.slug, pk=new_task.pk)


@login_required(login_url='/login/')
def change_task_status(request, lab, pk):
    user = get_object_or_404(Profile, user_id=request.user.id)
    task = get_object_or_404(Task, pk=pk, lab__slug=lab)

    if user.lab.slug != lab and not request.user.is_superuser:
        raise Http404

    if (user in task.executors.all() or user == task.creator or request.user.is_superuser) and request.method == 'POST':
        if request.is_ajax():
            if request.POST['type'] == 'start_work':
                task.status = 'IW'
            elif request.POST['type'] == 'stop_work_status_true':
                if task.status == 'IW':
                    task.status = 'CT'
                else:
                    return JsonResponse({'err': '?????? ???????? ?????????? ?????????????? ???????????? ???? ???????????? ???????????? ???????? "?? ????????????"'})
            elif request.POST['type'] == 'stop_work_status_false':
                if task.status == 'IW':
                    task.status = 'CF'
                else:
                    return JsonResponse({'err': '?????? ???????? ?????????? ?????????????? ???????????? ???? ???????????? ???????????? ???????? "?? ????????????"'})

            task.save()
            text = f'{user.name} ??????????????(a) ???????????? ???????????? ???? "{task.get_status_display()}"'
            task.add_robot_comment(text, user)
            return JsonResponse({'rez': 'status change'}, status=200)
