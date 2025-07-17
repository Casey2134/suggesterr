from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('test_connections/', views.test_connections, name='test_connections')
]