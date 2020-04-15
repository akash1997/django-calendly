from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('calender/', include('calender_mgmt.urls')),
    path('user/', include('user_mgmt.urls'))
]
