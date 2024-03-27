from django.shortcuts import redirect
from django.urls import path
from dashboard import views

urlpatterns = [
    path('', lambda request: redirect('print-queue'), name='index'),

    path('print-queue/', views.print_queue, name='print-queue'),
    path('print-queue-table/', views.print_queue_table, name='print-queue-table'),
    path('print-queue/action/', views.print_queue_action, name='print-queue-action'),

    path('users/', views.users, name='users'),
    path('users-table/', views.users_table, name='users-table'),
    path('users/action/', views.users_action, name='users-action'),

    path('cashbox/', views.cashbox, name='cashbox'),
    path('cashbox-table/', views.cashbox_table, name='cashbox-table'),
    path('cashbox/action/', views.cashbox_action, name='cashbox-action'),

    path('prices/', views.prices, name='prices'),
    path('prices-table/', views.prices_table, name='prices-table'),
    path('prices/action/', views.prices_action, name='prices-action'),

    path('kiosks/', views.kiosks, name='kiosks'),
    path('kiosks-table/', views.kiosks_table, name='kiosks-table'),
    path('kiosks/action/', views.kiosks_action, name='kiosks-action'),

    path('statistics/', views.statistics, name='statistics'),
    path('statistics-page/', views.statistics_page, name='statistics-page')
]
