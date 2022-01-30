from django.urls import path
from . import views

app_name = 'myapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_, name='Login'),
    path('logout', views.logout_, name='Logout'),
    path('registration', views.registration_, name='registration'),
    path('profile', views.profile, name='Profile'),
    path('profile/edit', views.edit_profile, name='Edit'),
    path('profile/<username>', views.profile, name='Prof'),
    path('read', views.read, name='Read'),
    path('get_users', views.get_couples, name='GetUsers'),
    path('get_messages', views.get_messages, name='GetMessages'),
    path('send_message', views.send_message, name='SendMessage')
]
