from django.urls import path

from .views import DistrictView

urlpatterns = [
    path('distrito/', DistrictView.as_view(), name='poder-judicial-district'),
]
