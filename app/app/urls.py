"""
app URL Configuration.
"""
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import (
    path,
    include,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('__reload__/', include('django_browser_reload.urls')),
    path('user/', include('core.urls')),
    path('', include('dashboard.urls')),
    path('api/', include('api.urls')),
    # path('url', include('app_name.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
