import datetime
import time

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from django.contrib.auth.models import User
from django.db import transaction

from .models import CalenderSlot


class SlotDataView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            start_time = datetime.datetime.strptime(request.data['start_time'], "%Y-%m-%dT%H:%M:%SZ")
        except KeyError:
            return Response(data="Invalid request data!", status=HTTP_400_BAD_REQUEST)
        end_time = start_time + datetime.timedelta(hours=1)
        if end_time < datetime.datetime.now():
            return Response(
                data="You have attempted to create a slot in the past. Please create one in the future!",
                status=HTTP_400_BAD_REQUEST
            )
        blocking_slot = CalenderSlot.objects.filter(belongs_to=request.user, end_time__gt=start_time)
        if blocking_slot:
            response_message = "Cannot create this slot as it conflicts with an existing slot between {} and {}.".format(
                blocking_slot[0].start_time, blocking_slot[0].end_time
            )
            return Response(data=response_message, status=HTTP_400_BAD_REQUEST)
        CalenderSlot.objects.create(belongs_to=request.user, start_time=start_time, end_time=end_time)
        return Response(data="Successfully created the calender slot.", status=HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        all_created_slots = CalenderSlot.objects.filter(belongs_to=request.user).values('id', 'start_time', 'end_time')
        return Response(data=all_created_slots, status=HTTP_200_OK)


class SlotDetailsView(APIView):
    def get(self, request, *args, **kwargs):
        if CalenderSlot.objects.filter(id=kwargs['id'], belongs_to=request.user).exists():
            slot_details = CalenderSlot.objects.filter(id=kwargs['id'], belongs_to=request.user).values(
                'id', 'start_time', 'end_time'
            )
        else:
            return Response(
                data="Requested calender slot not found, please check if the slot exists and belongs to you!",
                status=HTTP_400_BAD_REQUEST
            )
        return Response(data=slot_details, status=HTTP_200_OK)


class GetAvailableSlots(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        available_slots = CalenderSlot.objects.filter(
            start_time__gt=datetime.datetime.now(), booking_details=None
        ).values(
            'id', 'start_time', 'end_time'
        )
        return Response(data=available_slots, status=HTTP_200_OK)
