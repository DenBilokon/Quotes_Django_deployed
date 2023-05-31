from django.urls import path

from . import views

app_name = "super_quotes"

urlpatterns = [
    path('', views.home, name='home'),
    path('<int:page>', views.home, name='root_paginate'),
    path('author/<int:_id>', views.author_about, name='author_about'),
    path('add_quote/', views.add_quote, name='add_quote'),
    path('add_author/', views.add_author, name='add_author'),
    path('add_tag/', views.add_tag, name='add_tag'),
    path('tag/<int:_id>/', views.find_tag, name='find_tag'),
    path('tag/<str:_id>/', views.find_tag, name='find_tag'),
    path('search_quotes/', views.search_quotes, name='search_quotes'),
    path('parse_quotes/', views.parse_quotes, name='parse_quotes'),

]
