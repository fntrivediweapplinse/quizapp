from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_dashboard, name='quiz_dashboard'),
    path('start/', views.quiz_start, name='quiz_start'),
    path('question/<int:category_id>/', views.quiz_question, name='quiz_question'),
    path('result/<int:category_id>/', views.quiz_result, name='quiz_result'),
    path('leaderboard/', views.leaderboard_main, name='leaderboard_main'),
    # Removed the specific category leaderboard URL pattern
    # path('leaderboard/<int:category_id>/', views.leaderboard, name='leaderboard'),
    # The admin URLs are included separately in the main urls.py
] 