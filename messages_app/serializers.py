from rest_framework import serializers
import datetime


class AfricastalkingMessageSerializer(serializers.Serializer):
    _from = serializers.CharField(max_length=15, allow_null=False, min_length=10)
    to = serializers.CharField(max_length=15, allow_null=False, min_length=10)
    text = serializers.CharField()
    date = serializers.DateTimeField(default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    id = serializers.CharField(max_length=30)
    linkId = serializers.CharField(max_length=30)