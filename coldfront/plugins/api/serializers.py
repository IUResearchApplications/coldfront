from django.contrib.auth.models import User
from rest_framework import serializers
from coldfront.core.allocation.models import Allocation, AllocationAttribute


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


class AllocationAttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AllocationAttribute
        fields = ['url', 'value']


class AllocationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Allocation
        fields = ['url', 'resources', 'start_date', 'end_date', 'created', 'allocationattribute_set']
