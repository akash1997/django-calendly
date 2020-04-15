from django.urls import include, path

from .views import UserLoginView, UserRegisterView

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='user_mgmt_login'),
    path('register/', UserRegisterView.as_view(), name='user_mgmt_register')
]

