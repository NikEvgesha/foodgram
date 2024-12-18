from django.contrib import admin
from django.urls import include, path

from api.views import redirect_url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('url/<str:hash>/', redirect_url)
]
