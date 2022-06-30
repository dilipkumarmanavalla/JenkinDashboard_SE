from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView().get),
    path('console/', views.get_console_output)
]
