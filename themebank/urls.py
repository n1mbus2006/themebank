from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Каталог, заявки, сводка и служебные JSON-представления.
    path('', include('core.urls')),
    # Вход, регистрация, смена пароля (django.contrib.auth).
    path('', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Заголовки админки — чтобы в скриншотах было видно, о каком проекте речь.
admin.site.site_header = 'Банк тем курсовых и дипломных работ'
admin.site.site_title = 'Банк тем'
admin.site.index_title = 'Раздел администрирования'
