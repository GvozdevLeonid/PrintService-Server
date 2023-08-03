from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models


class AdminUser(BaseUserAdmin):
    ordering = ['id']
    list_display = ['phone_number', 'email', 'name', 'balance']
    search_fields = ['name', 'email', 'phone_number']
    list_filter = ["is_staff", 'allow_credit']
    readonly_fields = ["last_login"]
    fieldsets = (
        (('User'), {"fields": ('name', 'phone_number', 'email', 'balance', 'password', 'allow_credit', 'note', 'discount')}),
        (('Permissions'), {'fields': (
                                'is_active',
                                'is_staff',
                                'is_superuser',
                                'groups',
                                )
                            }),
        (('Last visited'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'email',
                'name',
                'balance',
                'password1',
                'password2',
                'note',
                'allow_credit',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                ),
        }),
    )


class AdminDiscount(admin.ModelAdmin):
    ordering = ['-id']
    list_display = ['name', 'percent']


class AdminPrint(admin.ModelAdmin):
    ordering = ['-id']
    list_display = ['date', 'identificator', 'status']


class AdminTransaction(admin.ModelAdmin):
    ordering = ['-id']
    list_display = ['date', 'identificator', 'amount', 'type']


class AdminKiosk(admin.ModelAdmin):
    ordering = ['-id']
    readonly_fields = ['configured_printers', 'key']


class AdminPrice(admin.ModelAdmin):
    ordering = ['-id']
    list_display = ['kiosk', 'print_settings', 'start_page', 'end_page', 'price']



admin.site.register(models.User, AdminUser)
admin.site.register(models.Discount, AdminDiscount)
admin.site.register(models.Print, AdminPrint)
admin.site.register(models.Transaction, AdminTransaction)
admin.site.register(models.Kiosk, AdminKiosk)
admin.site.register(models.Price, AdminPrice)
admin.site.register(models.EmailMessage)