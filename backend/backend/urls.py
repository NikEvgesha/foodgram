from api.views import redirect_url
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('url/<str:hash>/', redirect_url)
]
