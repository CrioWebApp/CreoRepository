from django.urls import path, re_path, include
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import DataValidation
from djoser.views import TokenCreateView, TokenDestroyView

urlpatterns = [
    path('dataValidation', DataValidation.as_view(), name='Action'),
    re_path(r'^apiAuth/token/?$', TokenCreateView.as_view(), name="login"),
    re_path(r'^apiAuth/token/logout/?$', TokenDestroyView.as_view(), name="logout"),
]

# urlpatterns = format_suffix_patterns(urlpatterns)