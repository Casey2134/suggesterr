from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.movie_list, name='list'),
    path('<int:movie_id>/', views.movie_detail, name='detail'),
    path('popular/', views.popular_movies, name='popular'),
    path('top-rated/', views.top_rated_movies, name='top_rated'),
]