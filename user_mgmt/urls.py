from django.urls import include, path

from .views import UserLoginView, UserRegisterView

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserRegisterView.as_view(), name='register')
]
