from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CommentDetailView,
    CommentModerateView,
    CommentReportCreateView,
    LoginView,
    LogoutView,
    MeView,
    NoteCommentListCreateView,
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
    path(
        'notes/<int:note_id>/comments/',
        NoteCommentListCreateView.as_view(),
        name='note-comments',
    ),
    path(
        'comments/<int:comment_id>/',
        CommentDetailView.as_view(),
        name='comment-detail',
    ),
    path(
        'comments/<int:comment_id>/reports/',
        CommentReportCreateView.as_view(),
        name='comment-report',
    ),
    path(
        'comments/<int:comment_id>/moderate/',
        CommentModerateView.as_view(),
        name='comment-moderate',
    ),
]

urlpatterns += router.urls
