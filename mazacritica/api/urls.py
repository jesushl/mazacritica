from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NoteViewSet, SourceViewSet, TagViewSet, UserCreate

router = DefaultRouter()
router.register('notes', NoteViewSet, basename='note')
router.register('tags', TagViewSet, basename='tag')
router.register('sources', SourceViewSet, basename='source')

urlpatterns = [
    path('register/', UserCreate.as_view(), name='user-create'),
]

urlpatterns += router.urls