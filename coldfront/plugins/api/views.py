from django.contrib.auth.models import User
from rest_framework import viewsets
from coldfront.plugins.api.serializers import UserSerializer, AllocationSerializer, AllocationAttributeSerializer
from rest_framework.permissions import IsAuthenticated
from coldfront.core.allocation.models import Allocation, AllocationAttribute

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class AllocationViewSet(viewsets.ModelViewSet):
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer
    permission_classes = [IsAuthenticated]


class AllocationAttributeViewSet(viewsets.ModelViewSet):
    queryset = AllocationAttribute.objects.all()
    serializer_class = AllocationAttributeSerializer
    permission_classes = [IsAuthenticated]