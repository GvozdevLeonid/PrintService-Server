from django.urls import (
    path,
    include,
)
from django.contrib.auth import views as auth_views
from core import views
urlpatterns = [
    path('registration/', views.registration, name='registration'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('set-password/', views.set_password, name='set-password'),
]