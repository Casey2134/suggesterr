from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/tmdb-search/', views.tmdb_search_api, name='tmdb_search_api'),
    path('health/', views.health_check, name='health_check'),
]