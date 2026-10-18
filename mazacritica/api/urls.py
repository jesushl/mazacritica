from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    LogoutView,
    MeView,
    NoteViewSet,
    RegisterView,
    SourceViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register('notes', NoteViewSet, basename='note')
router.register('tags', TagViewSet, basename='tag')
router.register('sources', SourceViewSet, basename='source')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
]

urlpatterns += router.urls
