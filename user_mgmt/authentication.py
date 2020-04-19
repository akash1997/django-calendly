from rest_framework.authentication import TokenAuthentication

"""Overridden the default TokenAuthentication class to change the keyword from Token to Bearer.

"""
class CustomTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"
