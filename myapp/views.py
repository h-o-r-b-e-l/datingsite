import os
from datetime import datetime
from json import dumps, loads
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from notifications.signals import notify
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User, Message, RelationsWith, Couples


# Create your views here.


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'profile_pic', )


class ProfilePictureForm(ModelForm):
    class Meta:
        model = User
        fields = ('profile_pic', )


class UserEdit(ModelForm):
    class Meta:
        model = User
        fields = ('username', 'profile_pic',)


def index(request):
    if request.user.is_authenticated:
        if not RelationsWith.objects.filter(user=request.user):
            RelationsWith(user=request.user).save()
    else:
        return render(request, 'base.html', {})
    context = {'profiles': ''}

    if request.method == 'POST':
        RelationsWith.objects.get(user=request.user).users.create(user=User.objects.get(id=request.POST['user']),
                                                                  is_liked=request.POST['liked'])
        next_user = User.objects.exclude(
            id__in=[i.user.id for i in RelationsWith.objects.get(user=request.user).users.all()]).exclude(
            profile_pic='').exclude(id=request.user.id)
        if next_user.count():
            context['profiles'] = {
                            'id': next_user[0].id,
                            'username': next_user[0].username,
                            'profile_pic': next_user[0].profile_pic.url
            }

        if request.POST['liked']:
            rel = RelationsWith.objects.filter(user=User.objects.get(id=request.POST['user']))
            if rel.count() > 0:
                rel = rel[0].users.filter(user=request.user)
                if rel.count() > 0:
                    if rel[0].is_liked:
                        usr = User.objects.get(id=request.POST['user'])
                        context['prev_user'] = {
                            'id': usr.id,
                            'username': usr.username,
                            'profile_pic': usr.profile_pic.url
                        }
                        couple = Couples()
                        couple.save()
                        couple.users.add(usr, request.user)
                        couple.save()
                        notify.send(request.user, recipient=usr, verb=dumps({
                            'profile_pic': request.user.profile_pic.url,
                            'username': request.user.username,
                            'type': 'match'
                        }))
                        notify.send(usr, recipient=request.user, verb=dumps({
                            'profile_pic': usr.profile_pic.url,
                            'username': usr.username,
                            'type': 'match'
                        }))
        return JsonResponse(context)

    next_user = User.objects.exclude(
        id__in=[i.user.id for i in RelationsWith.objects.get(user=request.user).users.all()]).exclude(
        profile_pic='').exclude(id=request.user.id)

    if next_user.count():
        context['profiles'] = next_user[0]
    return render(request, 'base.html', context)


def read(request):
    for i in request.user.notifications.unread()[:5]:
        i.mark_as_read()
    return HttpResponse()


def get_couples(request):
    context = {}
    users = Couples.objects.filter(users=request.user)
    for i in users:
        user = i.users.exclude(id=request.user.id)[0]
        context[user.username] = {
            'username': user.username,
            'profile_pic': user.profile_pic.url
        }
        if i.messages.count():
            last_msg = i.messages.order_by('-date')[0]
            context[user.username]['last_msg'] = {
                'from': last_msg.from_user.username,
                'msg': last_msg.text,
                'date': last_msg.date
            }
    return JsonResponse(context)


def get_messages(request):
    context = []
    msg = Couples.objects.filter(users=request.user).filter(users__username=request.POST['user'])[0].messages.order_by(
        '-date')[int(request.POST['num']):int(request.POST['num']) + 10]
    print(request.POST)
    for i in reversed(msg):
        context.append({
            'from': i.from_user.username,
            'msg': i.text,
            'date': f'{i.date.hour}:{f"0{str(i.date.minute)}" if i.date.minute < 10 else i.date.minute}'
        })
    return JsonResponse(context, safe=False)


def send_message(request):
    msg = Message(from_user=request.user, text=request.POST['text'], date=datetime.now())
    msg.save()
    usr = User.objects.get(username=request.POST['to'])
    Couples.objects.filter(users=request.user).filter(users=usr)[0].messages.add(msg)
    notify.send(request.user, recipient=usr, verb=dumps({
        'user': request.user.username,
        'type': 'message'
    }))
    notify.send(usr, recipient=request.user, verb=dumps({
        'user': usr.username,
        'type': 'message'
    }))
    return HttpResponse()


def login_(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('http://127.0.0.1:8000/')
        else:
            messages.info(request, 'Username or password is incorrect')
    context = {}
    return render(request, 'login.html', context)


def logout_(request):
    logout(request)
    return redirect('/login')


def registration_(request):
    form = UserForm()
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account was created! You joined to the society of reptiloids!')
            return redirect('/login')
    context = {'form': form}
    return render(request, 'registration.html', context)


def profile(request, username=''):
    if not request.user.is_authenticated:
        return redirect('/login')
    elif username == request.user.username:
        return redirect('/profile')
    if not username:
        user = request.user
    else:
        user = User.objects.filter(username=username)[0]
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('/profile')
        else:
            form = ProfilePictureForm(instance=request.user)
            return render(request, 'profile.html', {'form': form, 'user': user})
    else:
        form = ProfilePictureForm(instance=request.user)
        return render(request, 'profile.html', {'form': form, 'user': user})


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    form = UserEdit()
    if request.method == 'POST':
        if request.FILES:
            os.remove(request.user.profile_pic.path)
        if request.POST['username']:
            form = UserEdit(request.POST, request.FILES, instance=request.user)
        else:
            form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():

            form.save()
            return redirect('/profile')
    return render(request, 'edit.html', {'form': form})
