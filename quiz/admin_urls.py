from django.urls import path
from . import views

urlpatterns = [
    path('', views.admincrud, name='admincrud'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<slug:slug>/edit/', views.category_edit, name='category_edit'),
    path('categories/<slug:slug>/delete/', views.category_delete, name='category_delete'),
    path('questions/', views.question_list, name='question_list'),
    path('questions/create/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
] 