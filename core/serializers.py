from rest_framework import serializers
from core.models import (
    User,
    UserProfile,
    MonitorStock,
    PortHistory,
)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        if 'profile' in validated_data.keys():
            profile_data = validated_data.pop('profile')
        else:
            profile_data = {}
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        profile = instance.profile

        instance.email = validated_data.get('email', instance.email)
        instance.save()

        profile.title = profile_data.get('title', profile.title)
        profile.dob = profile_data.get('dob', profile.dob)
        profile.address = profile_data.get('address', profile.address)
        profile.country = profile_data.get('country', profile.country)
        profile.city = profile_data.get('city', profile.city)
        profile.zip = profile_data.get('zip', profile.zip)
        profile.save()

        return instance

class MonitorStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorStock
        fields = '__all__'

class PortHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortHistory
        fields = '__all__'