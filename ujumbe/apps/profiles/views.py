from rest_framework import permissions
from rest_framework.generics import ListAPIView
from ujumbe.apps.profiles.models import Profile
from ujumbe.apps.profiles.serializers import ProfileSerializer


# Create your views here.
class ListProfilesView(ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAdminUser,)
