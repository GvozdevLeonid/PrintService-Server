from django.urls import (
    path,
)
from api import views

urlpatterns = [
    path('add-kiosk/<uuid:key>/', views.add_kiosk, name='add-kiosk'),
    path('kiosk-status/<uuid:key>/', views.kiosk_status, name='kiosk-status'),
    path('check-user/<uuid:key>/', views.check_user, name='check-user'),
    path('new-print/<uuid:key>/', views.new_print, name='new-print'),
    path('check-print/<uuid:key>/', views.check_print, name='check-print'),
    path('email-files-list/<uuid:key>/', views.email_files_list, name='email-files-list'),
    path('download-file-from-email/<uuid:key>/', views.download_file_from_email, name='download-file-from-email'),

]