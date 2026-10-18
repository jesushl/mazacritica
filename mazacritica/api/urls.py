from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CandidacyViewSet,
    CandidateViewSet,
    CommentDetailView,
    CommentModerateView,
    CommentReportCreateView,
    ElectionViewSet,
    ElectionZoneViewSet,
    LoginView,
    LogoutView,
    MeView,
    NoteCommentListCreateView,
    NoteViewSet,
    OfficeViewSet,
    PostalCodeSearchView,
    PostalCodeViewSet,
    PostalCodeZoneMappingViewSet,
    RegisterView,
    SourceViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register('notes', NoteViewSet, basename='note')
router.register('tags', TagViewSet, basename='tag')
router.register('sources', SourceViewSet, basename='source')
router.register('elections', ElectionViewSet, basename='election')
router.register('offices', OfficeViewSet, basename='office')
router.register('candidates', CandidateViewSet, basename='candidate')
router.register('candidacies', CandidacyViewSet, basename='candidacy')
router.register('postal-codes', PostalCodeViewSet, basename='postal-code')
router.register('election-zones', ElectionZoneViewSet, basename='election-zone')
router.register(
    'postal-code-zone-mappings',
    PostalCodeZoneMappingViewSet,
    basename='postal-code-zone-mapping',
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path(
        'postal-code-search/',
        PostalCodeSearchView.as_view(),
        name='postal-code-search',
    ),
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
