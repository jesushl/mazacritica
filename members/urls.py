from django.urls import path

from members.views import UserRegiterView
# Views


urlpatterns = [
   path('register/', UserRegiterView.as_view(), name='register' )
]
