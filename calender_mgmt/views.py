import datetime
import time

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import CalenderSlot, SlotBooking


class SlotDataView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            start_time = datetime.datetime.strptime(request.data['start_time'], "%Y-%m-%dT%H:%M:%SZ")
        except KeyError:
            return Response(data="Could not find the request key 'start_time'!", status=HTTP_400_BAD_REQUEST)
        except ValueError:
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
        all_created_slots = CalenderSlot.objects.filter(belongs_to=request.user)
        response_data = []
        for slot_detail in all_created_slots:
            slot_data = {
                "id": slot_detail.id,
                "start_time": str(slot_detail.start_time),
                "end_time": str(slot_detail.end_time)
            }
            try:
                slot_detail.booking_details
            except:
                slot_data['is_booked'] = False
            else:
                slot_data['is_booked'] = True
            response_data.append(slot_data)
        return Response(data=response_data, status=HTTP_200_OK)


class SlotDetailsView(APIView):
    def get(self, request, *args, **kwargs):
        if CalenderSlot.objects.filter(id=kwargs['id'], belongs_to=request.user).exists() is False:
            return Response(
                data="Requested calender slot not found, please check if the slot exists and belongs to you!",
                status=HTTP_404_NOT_FOUND
            )
        slot_details = CalenderSlot.objects.select_related('booking_details__booked_by').get(
            id=kwargs['id'], belongs_to=request.user
        )
        response_data = {
            "id": slot_details.id,
            "start_time": str(slot_details.start_time),
            "end_time": str(slot_details.end_time)
        }
        try:
            booking_details = slot_details.booking_details
        except:
            response_data['is_booked'] = False
        else:
            booked_by = "Anonymous User"
            if booking_details.booked_by:
                booked_by = booking_details.booked_by.username
            response_data.update({
                "is_booked": True,
                "booking_id": booking_details.id,
                "booked_by": booked_by,
                "booked_at": str(booking_details.booked_at),
                "description": booking_details.description
            })
        return Response(data=response_data, status=HTTP_200_OK)


class GetAvailableSlots(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        available_slots = CalenderSlot.objects.filter(start_time__gt=timezone.now(), booking_details=None)
        response_data = []
        for slot_details in available_slots:
            response_data.append({
                "id": slot_details.id,
                "start_time": str(slot_details.start_time),
                "end_time": str(slot_details.end_time),
                "belongs_to": slot_details.belongs_to.username
            })
        return Response(data=response_data, status=HTTP_200_OK)


class BookSlotView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            slot = CalenderSlot.objects.get(id=kwargs['id'])
        except Calenderslot.DoesNotExist:
            return Response(data="The requested slot not found! Please check again!", status=HTTP_404_NOT_FOUND)
        if SlotBooking.objects.filter(slot=slot).exists():
            return Response(
                data="The requested slot is already booked! Please try another slot!", status=HTTP_400_BAD_REQUEST
            )
        if slot.end_time < timezone.now():
            return Response(
                data="The slot you are trying to book is in the past, please try booking another slot!",
                status=HTTP_400_BAD_REQUEST
            )
        try:
            booking_description = request.data['description']
        except KeyError:
            return Response(
                data="The key 'description' not found in the request body! Please try again!",
                status=HTTP_400_BAD_REQUEST
            )
        slot_booking_details = SlotBooking.objects.create(slot=slot, booked_by=request.user, description=booking_description)
        return Response(
            data="Booked the slot successfully! Your Booking ID is {}".format(slot_booking_details.id), status=HTTP_200_OK
        )


class CreateSlotsForIntervalView(APIView):
    def post(self, request, *args, **kwargs):
        interval_start = datetime.datetime.strptime(request.data['interval_start'], "%Y-%m-%dT%H:%M:%SZ")
        interval_stop = datetime.datetime.strptime(request.data['interval_stop'], "%Y-%m-%dT%H:%M:%SZ")
        if (interval_start.day != interval_stop.day) or (interval_start.month != interval_stop.month) or (interval_start.year != interval_stop.year):
            return Response(data="The interval days do not match! Please try again!", status=HTTP_400_BAD_REQUEST)

        slot_start_time = interval_start
        slot_end_time = slot_start_time + datetime.timedelta(hours=1)
        interval_date = datetime.date(slot_start_time.year, slot_start_time.month, slot_start_time.day)
        queryset = CalenderSlot.objects.filter(belongs_to=request.user).filter(start_time__date=interval_date)
        while slot_end_time <= interval_stop:
            if not queryset.filter(
                (Q(start_time__lt=slot_end_time) & Q(start_time__gte=slot_start_time)) | 
                (Q(end_time__gt=slot_start_time) & Q(end_time__lte=slot_end_time)),
                start_time__date=interval_date
            ):
                CalenderSlot.objects.create(belongs_to=request.user, start_time=slot_start_time, end_time=slot_end_time)
            slot_start_time = slot_end_time
            slot_end_time = slot_end_time + datetime.timedelta(hours=1)
        return Response(data="Slots created successfully!", status=HTTP_200_OK)
