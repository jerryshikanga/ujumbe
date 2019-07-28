import logging

from django.conf import settings
from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import serializers

from ujumbe.apps.messaging.models import IncomingMessage, Message, OutgoingMessages

logger = logging.getLogger(__name__)


class TelerivetSerializer(serializers.Serializer):
    event = serializers.CharField(required=True)
    secret = serializers.CharField(required=True)

    def validate(self, attrs):
        validated_data = super(TelerivetSerializer, self).validate(attrs)
        event, secret = attrs["event"], attrs["secret"]
        if secret != settings.TELERIVET_WEBHOOK_SECRET:
            raise serializers.ValidationError("Invalid webhook secret.")
        if event not in ["incoming_message", "send_status"]:
            raise serializers.ValidationError("Unknown event.")
        if event == "send_status":
            required_fields = ["status", "id"]
        elif event == "incoming_message":
            required_fields = ["from_number", "to_number", "content", "id"]
        else:
            required_fields = []
        for k in required_fields:
            if k not in self.initial_data:
                raise serializers.ValidationError("For {} event {} has to be provided.".format(event, k))
        return validated_data

    def save(self, **kwargs):
        event = self.validated_data["event"]
        if event == "incoming_message":
            shortcode = self.initial_data["to_number"]
            shortcode = shortcode if shortcode.startswith("+") else "+{}".format(shortcode)
            message = IncomingMessage.objects.create(
                phonenumber=self.initial_data["from_number"],
                shortcode=shortcode,
                text=self.initial_data["content"],
                provider_id=self.initial_data["id"],
                handler=Message.MessageProviders.Telerivet
            )
        elif event == 'send_status':
            message = OutgoingMessages.objects.filter(provider_id=self.initial_data["id"]).first()
            if message is not None:
                message.delivery_status = self.initial_data.get('status')
                message.failure_reason = self.initial_data.get('error_message', None)
                message.save()
        else:
            message = Message()
        return message


class AfricastalkingIncomingMessageSerializer(serializers.Serializer):
    # from_number = serializers.CharField(required=True, ) # cant
    # include this due to conflict with pythons internals
    to = serializers.CharField(required=True, )
    text = serializers.CharField(required=True)
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    id = serializers.CharField(required=True)
    linkId = serializers.CharField(required=True)

    def validate(self, attrs):
        validated_data = super(AfricastalkingIncomingMessageSerializer, self).validate(attrs)
        if "from" not in self.initial_data:
            raise serializers.ValidationError("From telephone has to be provided")
        validate_international_phonenumber(self.initial_data["from"])
        return validated_data

    def save(self, **kwargs):
        data = self.validated_data
        shortcode = str(data.pop("to"))
        shortcode = shortcode if shortcode.startswith("+") else "+{}".format(shortcode)
        logger.error("Data {}".format(data))
        data.pop("linkId")
        data["phonenumber"] = data.pop("from")
        data["shortcode"] = shortcode
        data["handler"] = Message.MessageProviders.Africastalking
        return IncomingMessage.objects.create(**data)


class AfricastalkingOutgoingMessageSerializer(serializers.Serializer):
    phoneNumber = serializers.CharField(required=True)
    status = serializers.CharField(required=True)
    id = serializers.CharField(required=True)
    networkCode = serializers.CharField(required=True)

    def validate(self, attrs):
        validated_data = super(AfricastalkingOutgoingMessageSerializer, self).validate(attrs)
        if not OutgoingMessages.objects.filter(provider_id=self.initial_data["id"],
                                               handler=Message.MessageProviders.Africastalking).exists():
            raise serializers.ValidationError("Message does not exist")
        return validated_data

    def save(self, **kwargs):
        message = OutgoingMessages.objects.filter(provider_id=self.validated_data["id"],
                                                  handler=Message.MessageProviders.Africastalking).first()
        message.delivery_status = self.validated_data["status"]
        message.save()
