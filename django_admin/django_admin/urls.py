from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

handler404 = core_views.handler404
handler500 = core_views.handler500
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
