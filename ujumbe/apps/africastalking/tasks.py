from ujumbe.apps.profiles.models import Profile
from ujumbe.apps.africastalking.models import IncomingMessage


def process_incoming_messages(self):
    unprocessed_incoming_messages = IncomingMessage.objects.filter(processed=False)
    for message in unprocessed_incoming_messages:
        # processing will be done here
        pass
