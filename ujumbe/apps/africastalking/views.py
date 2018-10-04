from djchoices import DjangoChoices, ChoiceItem
import datetime
import json

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from djchoices import DjangoChoices, ChoiceItem

from ujumbe.apps.africastalking.models import IncomingMessage, OutgoingMessages


# Create your views here.
# Create your views here.
class MessageKeywords(DjangoChoices):
    Register = ChoiceItem("REGISTER")
    Weather = ChoiceItem("WEATHER")
    Subscribe = ChoiceItem("SUBSCRIBE")
    Unsubscribe = ChoiceItem("UNSUBSCRIBE")
    Location = ChoiceItem("LOCATION")
    Forecast = ChoiceItem("FORECAST")


class AfricastalkingMessageCallback(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AfricastalkingMessageCallback, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        try:
            request_data = json.loads(request.body)
            from_telephone = request_data.get("from", "")
            to_telephone = request_data.get("to", "")
            text = request_data.get("text", "")
            date = request_data.get("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            africastalking_id = request_data.get("id", "")
            link_id = request_data.get("linkId", "")

            # save message
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

            parts = incoming_message.text.split(sep=" ")
            parts = [str(part).upper() for part in parts]

            keyword = parts[0]

            # If user has no account, prompt registration and exit
            if not Profile.objects.filter(telephone=incoming_message.phonenumber).exists():
                if keyword == MessageKeywords.Register:
                    first_name = parts[1] if parts[1] else None
                    last_name = parts[2] if parts[2] else None
                    if first_name is not None and last_name is not None:
                        response = None
                        create_customer_account.delay(first_name=first_name, last_name=last_name,
                                                      phonenumber=incoming_message.phonenumber)
                    else:
                        response = "You are required to fill both first and last name"
                else:
                    response = "You do not have an account, please create one."
                send_sms.delay(phonenumber=incoming_message.phonenumber, text=response)
                return HttpResponse(status=200)

            profile = Profile.objects.get(telephone=incoming_message.phonenumber)

            # actions for users with accounts
            if keyword == MessageKeywords.Weather:
                summary = False if parts[1].upper() == "DETAILED" else True
                if Profile.objects.filter(telephone=incoming_message.phonenumber).exists():
                    if profile.location is None:
                        response = "Please enter your location."
                    else:
                        location = profile.location
                        weather = CurrentWeather.objects.get(
                            location=location
                        )
                        response = weather.summary if summary else weather.detailed
                else:
                    response = "You do not have an account, please create one."
            elif keyword == MessageKeywords.Location:
                location_str = parts[1]
                location, created = Location.objects.get_or_create(name=location_str)
                profile.location = location
                profile.save()
                response = "Your location has been saved successfully"
            # TODO : Implement forecast
            # elif keyword == "FORECAST":
            #     pass
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
                    response = subscription.sms_description
                else:
                    response = "You already have a similar subscription."

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
                response = "You have deactivated {} subscriptions.".format(subscriptions.count())

            else:
                keywords_list = ""
                for keyword in MessageKeywords.choices:
                    keywords_list.join(str(keyword[0]))
                response = "Your entry {} is invalid. Try again with either {}".format(keyword, keywords_list)
            if response is not None :
                send_sms.delay(phonenumber=incoming_message.phonenumber, text=response)
            return HttpResponse(status=200)
        except Exception as e:
            logging.error(e)
            return HttpResponse(status=400)
