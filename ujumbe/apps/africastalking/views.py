import datetime
import json
import logging
import re
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from djchoices import DjangoChoices, ChoiceItem
from ujumbe.apps.weather.tasks import send_user_current_location_weather
from ujumbe.apps.africastalking.models import IncomingMessage, UssdSession
from ujumbe.apps.profiles.models import Profile, Subscription
from ujumbe.apps.profiles.tasks import send_sms, create_customer_account, update_profile_location
from ujumbe.apps.weather.models import CurrentWeather, Location
from ujumbe.apps.weather.utils import get_weather_forecast_periods


# Create your views here.
# Create your views here.
class MessageKeywords(DjangoChoices):
    Register = ChoiceItem("REGISTER")
    Weather = ChoiceItem("WEATHER")
    Subscribe = ChoiceItem("SUBSCRIBE")
    Unsubscribe = ChoiceItem("UNSUBSCRIBE")
    Location = ChoiceItem("LOCATION")
    Forecast = ChoiceItem("FORECAST")


class ATMessageCallbackView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ATMessageCallbackView, self).dispatch(*args, **kwargs)

    def get_incoming_message_object(self, request_data):
        from_telephone = request_data.get("from", None)
        to_telephone = request_data.get("to", None)
        text = request_data.get("text", None)
        date = request_data.get("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        africastalking_id = request_data.get("id", None)
        link_id = request_data.get("linkId", None)

        # save message if not exist
        if not IncomingMessage.objects.filter(africastalking_id=africastalking_id).exists():
            incoming_message = IncomingMessage.objects.create(
                phonenumber=from_telephone,
                shortcode=to_telephone,
                text=text,
                africastalking_id=africastalking_id,
                link_id=link_id,
            )
        else:
            incoming_message = IncomingMessage.objects.filter(africastalking_id=africastalking_id).first()
            if from_telephone is not None:
                incoming_message.phonenumber = from_telephone
            if to_telephone is not None:
                incoming_message.shortcode = to_telephone
            if text is not None:
                incoming_message.text = text
            if link_id is not None:
                incoming_message.link_id = link_id
            incoming_message.save()
        return incoming_message

    def post(self, request, *args, **kwargs):
        try:
            request_data = json.loads(request.body)
            incoming_message = self.get_incoming_message_object(request_data)
            parts = incoming_message.text.split(sep=" ")
            parts = [str(part).upper() for part in parts]
            keyword = parts[0]

            response = ""
            if Profile.objects.filter(telephone=incoming_message.phonenumber).exists():
                profile = Profile.objects.get(telephone=incoming_message.phonenumber)

                if keyword == MessageKeywords.Register:
                    response += "You are already registered. "
                elif keyword == MessageKeywords.Weather:
                    summary = False if parts[1].upper() == "DETAILED" else True
                    weather = CurrentWeather.objects.filter(
                        location=profile.location
                    ).order_by("-created").first()
                    response += weather.summary if summary else weather.detailed
                elif keyword == MessageKeywords.Location:
                    location_str = parts[1]
                    update_profile_location.delay(phonenumber=incoming_message.phonenumber, location_str=location_str)
                    response += "Your request has been received successfully. "
                elif keyword == MessageKeywords.Subscribe:
                    subscription_type = parts[1]
                    frequency = parts[2]
                    location = parts[3] if parts[3] is not None else profile.location
                    subscription, created = Subscription.objects.get_or_create(
                        profile=profile,
                        subscription_type=subscription_type,
                        frequency=frequency,
                        location=location
                    )
                    if created:
                        response += subscription.sms_description
                    else:
                        response += "You already have a similar subscription. "
                elif keyword == MessageKeywords.Unsubscribe:
                    subscriptions = Subscription.objects.filter(
                        profile=profile
                    )
                    subscription_type = parts[1] if parts[1] is not None else None
                    if subscription_type: subscriptions.filter(subscription_type__iexact=subscription_type)

                    frequency = parts[2] if parts[2] is not None else None
                    if frequency: subscriptions.filter(frequency=frequency)

                    location = parts[3] if parts[3] is not None else None
                    if location: subscriptions.filter(location=location)

                    [subscription.deactivate() for subscription in subscriptions]
                    response += "You have deactivated {} subscriptions. ".format(subscriptions.count())
                elif keyword == MessageKeywords.Forecast:
                    response += "This feature is coming soon! Stay put. "
                else:
                    keywords = ""
                    for key in MessageKeywords.choices:
                        keywords += key[1] + " "
                    response += "Your entry {} is invalid. Try again with either {}. ".format(incoming_message.text,
                                                                                              keywords)

                # additional checks for unset fields
                if profile.location is None:
                    response += "Remember to set your location. "
                if profile.user is not None:
                    if profile.user.email is None or str(profile.user.email).replace(" ", "") == "":
                        response += "Remember to set your email. "

            else:
                if keyword == MessageKeywords.Register:
                    first_name = parts[1] if parts[1] else None
                    last_name = parts[2] if parts[2] else None
                    if first_name is not None and last_name is not None:
                        response += "Account registration in progress, you will be notified once complete. "
                        create_customer_account.delay(first_name=first_name, last_name=last_name,
                                                      phonenumber=incoming_message.phonenumber)
                    else:
                        response += "You are required to fill both first and last name. "
                else:
                    response += "You do not have an account, please create one. "
            send_sms.delay(phonenumber=incoming_message.phonenumber, text=response)
            return HttpResponse(status=200, content=response, content_type="text/plain")
        except Exception as e:
            logging.error(e)
            return HttpResponse(status=400)


class AtUssdcallbackView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        super(AtUssdcallbackView, self).dispatch(*args, **kwargs)



    def post(self, request, *args, **kwargs):
        # Reads the variables sent via POST
        data = json.loads(request.body)
        session_id = data.get("sessionId", None)
        service_code = data.get("serviceCode", None)
        phonenumber = data.get("phoneNumber", None)
        text = data.get("text", "")
        text = str(text).strip()

        if session_id is None or phonenumber is None:
            return HttpResponse(status=400)

        UssdSession.objects.get_or_create(
            session_id=session_id,
            service_code=service_code,
            phonenumber=phonenumber,
            text=text
        )

        if Profile.objects.filter(telephone=phonenumber).exists():
            data = "CON You don't have an account. Choose an option : \n"
            data += "0. Register \n"
            data += "99. Exit\n"
        else:
            profile = Profile.objects.filter(telephone=phonenumber).first()
            # no text entered by user
            if text == "":
                data = "CON Choose Operation\n"
                data += "1. Current Weather Data\n"
                data += "2. Forecast Weather Data\n"
                data += "3. My Account\n"

            elif text == "1":
                data = "CON : Choose location\n"
                data += "1. Enter location\n"
                if profile.location is not None:
                    data += "2. Default location ({})\n".format(profile.location.name)

            elif text == "1*2":
                data = "END Your current location weather will be sent to you shortly via SMS."
                send_user_current_location_weather.delay(phonenumber=phonenumber)

            elif text == "1*1":
                data = "CON Enter location name."

            elif re.match("1*1*", text) is not None and len(text.split("*")) == 3:
                parts = text.split("*")
                location = Location.try_resolve_location_by_name(name=parts[2])
                if location is None:
                    data = "END Location could not be determined"
                else:
                    data = "END Your current location weather will be sent to you shortly via SMS."
                    send_user_current_location_weather.delay(phonenumber=phonenumber, location_id=location.id)

            elif text == "2":
                data = "CON : Choose location\n"
                data += "1. Enter location\n"
                if profile.location is not None:
                    data += "2. Default location ({})\n".format(profile.location.name)

            elif text == "2*1":
                data = "CON Enter location name."

            elif re.match("2*1*", text) is not None and len(text.split("*")) == 3:
                parts = text.split("*")
                location = Location.try_resolve_location_by_name(name=parts[2])
                if location is None:
                    data = "END Location could not be determined"
                else:
                    data = "CON Choose period."
                    data += get_weather_forecast_periods()

            elif text == "2*2":
                data = "CON Choose period."
                data += get_weather_forecast_periods()

            # TODO : Implement step when forecast data has been picked
            # TODO : Implement Accounts
            # TODO : Implement Subscriptions

        return HttpResponse(status=200, content_type="text/plain", content=data)
