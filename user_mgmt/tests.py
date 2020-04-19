from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.test import APITestCase

from .constants import ResponseMessages


class UserRegisterationTestCase(APITestCase):
    def setUp(self):
        self.email = 'test@mail.com'
        self.password = 'password'

    def test_register_correct_keys(self):
        url = reverse('user_mgmt:register')
        data = {'email': self.email, 'password': self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username=self.email).exists())

    def test_register_incorrect_keys(self):
        url = reverse('user_mgmt:register')
        data = {'emai': self.email, 'passwor': self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.INVALID_REGISTERATION_KEYS)
        self.assertEqual(User.objects.count(), 0)
        self.assertFalse(User.objects.filter(username=self.email).exists())

    def test_register_with_existing_email(self):
        User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        url = reverse('user_mgmt:register')
        data = {'email': self.email, 'password': self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.ALREADY_REGISTERED)
        self.assertEqual(User.objects.count(), 1)


class UserLoginTestCase(APITestCase):
    def setUp(self):
        self.username = 'test@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.username, email=self.username, password=self.password
        )
        self.token = Token.objects.create(user=self.user).key
    
    def test_login_correct_credentials(self):
        url = reverse('user_mgmt:login')
        data = {'username': self.username, 'password': self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data['token'], self.token)
    
    def test_login_incorrect_credentials(self):
        url = reverse('user_mgmt:login')
        data = {'username': self.username, 'password': "abc"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, ResponseMessages.INVALID_LOGIN_DATA)
    
    def test_login_incorrect_keys(self):
        url = reverse('user_mgmt:login')
        data = {'usernames': self.username, 'passwor': self.password}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, ResponseMessages.INVALID_LOGIN_DATA)
