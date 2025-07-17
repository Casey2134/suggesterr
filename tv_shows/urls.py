from django.urls import path
from . import views

app_name = 'tv_shows'

urlpatterns = [
    path('', views.tv_show_list, name='list'),
    path('<int:tv_show_id>/', views.tv_show_detail, name='detail'),
    path('popular/', views.popular_tv_shows, name='popular'),
    path('top-rated/', views.top_rated_tv_shows, name='top_rated'),
]