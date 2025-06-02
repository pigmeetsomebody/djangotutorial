# coding: utf-8
from django.urls import path
from . import views

app_name = 'group'

urlpatterns = [
    path('create-group/', views.CreateGroup.as_view(), name='create_group'),
]
