from rest_framework import serializers
from ujumbe.apps.profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Profile
        fields = ("user", "balance", "telephone")
        read_only_fields = ("user", "balance")
