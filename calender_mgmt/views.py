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
            slot_date = datetime.datetime.strptime(request.data['slot_date'], "%Y-%m-%d")
            start_time = datetime.datetime.strptime(request.data['start_time'], "%H:%M")
        except KeyError:
            return Response(data="Invalid request data!", status=HTTP_400_BAD_REQUEST)
        slot_datetime = datetime.datetime(
            year=slot_date.year, month=slot_date.month, day=slot_date.day, hour=start_time.hour, minute==start_time.min
        )
        if slot_datetime < datetime.datetime.now():
            return Response(data="New slots can be created for future time only.", status=HTTP_400_BAD_REQUEST)
        if CalenderSlot.objects.filter(belongs_to=request.user, slot_date=slot_date, end_time__gt=start_time).exists():
            return Response(
                data="Cannot create the slot as it conflicts with an existing slot.", status=HTTP_400_BAD_REQUEST
            )
        CalenderSlot.objects.create(belongs_to=request.user, slot_date=slot_date, start_time=start_time)
        return Response(data="Successfully created the calender slot.", status=HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        all_created_slots = CalenderSlot.objects.filter(belongs_to=request.user).values(
            'id', 'slot_date', 'start_time', 'end_time'
        )
        return Response(data=all_created_slots, status=HTTP_200_OK)
