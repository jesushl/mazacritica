# URLs
from django.shortcuts import render
from django.urls import reverse_lazy
# Views
from django.views import generic
# Forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm
# Models
from django.contrib.auth.forms import User


class UserRegiterView(generic.CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

