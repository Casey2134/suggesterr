from django.urls import path
from . import views
from . import health_views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('health/', health_views.health_check, name='health_check'),
    path('ready/', health_views.ready_check, name='ready_check'),
    path('live/', health_views.liveness_check, name='liveness_check'),
]