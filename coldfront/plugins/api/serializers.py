from django.contrib.auth.models import User
from rest_framework import serializers
from coldfront.core.allocation.models import Allocation, AllocationAttribute


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']
        extra_kwargs = {'url': {'view_name': 'api:user-detail'}}


class AllocationAttributeSerializer(serializers.HyperlinkedModelSerializer):
    allocation_attribute_type = serializers.SlugRelatedField(read_only=True, slug_field='name')
    class Meta:
        model = AllocationAttribute
        fields = ['allocation', 'allocation_attribute_type', 'value']


class AllocationSerializer(serializers.HyperlinkedModelSerializer):
    resources = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    class Meta:
        model = Allocation
        fields = ['url', 'resources', 'start_date', 'end_date', 'created', 'allocationattribute_set']
        extra_kwargs = {
            'url': {'view_name': 'api:allocation-detail'},
            'allocationattribute_set': {'view_name': 'api:allocationattribute-detail'}
        }
