from django.urls import path, include
from rest_framework import routers
from coldfront.plugins.api.views import UserViewSet, AllocationViewSet, AllocationAttributeViewSet


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'allocations', AllocationViewSet)
router.register(r'allocations-attributes', AllocationAttributeViewSet)

# app_name='api'
urlpatterns = [
    path('', include(router.urls)),
]
