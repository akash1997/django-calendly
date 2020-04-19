import datetime
import time

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .constants import ResponseMessages
from .functions import generate_google_calendar_link
from .models import CalenderSlot, SlotBooking


class SlotDataView(APIView):
    def post(self, request, *args, **kwargs):
        """Creates a bookable slot for the logged in user.

        Creates a slot of one hour from the provided start time available for booking for the logged in user.
        The slot is created if it does not conflict with any existing slot and if the end time of the slot is greater than the
        current time, because the slot should be available to book after it is created.

        """
        try:
            start_time = datetime.datetime.strptime(request.data['start_time'], "%Y-%m-%dT%H:%M:%SZ")
        except KeyError:
            return Response(data=ResponseMessages.MISSING_KEY.format("start_time"), status=HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response(data=ResponseMessages.INVALID_DATA, status=HTTP_400_BAD_REQUEST)
        end_time = start_time + datetime.timedelta(hours=1)
        if end_time < datetime.datetime.now():
            return Response(data=ResponseMessages.CREATE_FUTURE_SLOTS, status=HTTP_400_BAD_REQUEST)
        blocking_slot = CalenderSlot.objects.filter(belongs_to=request.user, end_time__gt=start_time)
        if blocking_slot:
            response_message = ResponseMessages.CONFLICTING_SLOT.format(blocking_slot[0].start_time, blocking_slot[0].end_time)
            return Response(data=response_message, status=HTTP_400_BAD_REQUEST)
        calender_slot = CalenderSlot.objects.create(belongs_to=request.user, start_time=start_time, end_time=end_time)
        return Response(data={'id': calender_slot.id}, status=HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        """Returns all the slot details created by the logged in user.

        Returns the id, start and end time of the slot, and if the slot is booked for each of the slots.

        """
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
        """Gives a detailed information of the specified slot, including details of the booking if it is booked.

        The booking status is determined by accessing the `booking_details` from the current slot object, which is
        set only when the slot is booked. If it was booked anonymously, the booked by field is set to the string
        `Anonymous User`, else the username of the registered user is set in the response data.

        """
        if CalenderSlot.objects.filter(id=kwargs['id'], belongs_to=request.user).exists() is False:
            return Response(data=ResponseMessages.CALENDER_SLOT_NOT_FOUND, status=HTTP_404_NOT_FOUND)
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

    def delete(self, request, *args, **kwargs):
        """Deletes the requested calender slot.

        """
        try:
            CalenderSlot.objects.get(id=kwargs['id'], belongs_to=request.user).delete()
        except CalenderSlot.DoesNotExist:
            return Response(data=ResponseMessages.CALENDER_SLOT_NOT_FOUND, status=HTTP_404_NOT_FOUND)
        else:
            return Response(status=HTTP_200_OK)


class GetAvailableSlots(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """Lists all the available slots of the requested user.
        
        This API is accessible by both registered and anonymous users. So no authentication check is done.

        """
        try:
            user = User.objects.get(id=kwargs['user_id'])
        except User.DoesNotExist:
            return Response(data=ResponseMessages.USER_NOT_FOUND, status=HTTP_404_NOT_FOUND)
        available_slots = CalenderSlot.objects.filter(
            start_time__gt=timezone.now(), booking_details=None, belongs_to=user
        )
        response_data = []
        for slot_details in available_slots:
            response_data.append({
                "id": slot_details.id,
                "start_time": str(slot_details.start_time),
                "end_time": str(slot_details.end_time)
            })
        return Response(data=response_data, status=HTTP_200_OK)


class BookSlotView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """Books the requested slot. This API is accessible for both anonymous and registered users.

        Checks if the requested slot exists and is not booked yet. Booking is only allwed for slots in the future.
        Returns the booking id and a link to add the event to Google Calendar.

        """
        try:
            slot = CalenderSlot.objects.get(id=kwargs['id'])
        except Calenderslot.DoesNotExist:
            return Response(data=ResponseMessages.CALENDER_SLOT_NOT_FOUND, status=HTTP_404_NOT_FOUND)
        if SlotBooking.objects.filter(slot=slot).exists():
            return Response(data=ResponseMessages.CALENDER_SLOT_ALREADY_BOOKED, status=HTTP_400_BAD_REQUEST)
        if slot.end_time < timezone.now():
            return Response(data=ResponseMessages.CALENDER_SLOT_EXPIRED, status=HTTP_400_BAD_REQUEST)
        try:
            booking_description = request.data['description']
        except KeyError:
            return Response(data=ResponseMessages.MISSING_KEY.format("description"), status=HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            slot_booking_details = SlotBooking.objects.create(slot=slot, booked_by=request.user, description=booking_description)
            response_data = {
                "id": slot_booking_details.id,
                "add_to_google_calendar": generate_google_calendar_link(slot_booking_details)
            }
            return Response(data=response_data, status=HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Deletes the requested booking.

        Only the bookings made by registered users can be deleted. This is to prevent cases where anyone can delete bookings of others.

        """
        if request.user is None:
            return Response(data=ResponseMessages.REGISTERATION_REQUIRED, status=HTTP_401_UNAUTHORIZED)
        booking = SlotBooking.objects.filter((Q(booked_by=request.user) | Q(slot__belongs_to=request.user)), id=kwargs['id'])
        if len(booking) == 0:
            return Response(data=ResponseMessages.BOOKING_NOT_FOUND, status=HTTP_404_NOT_FOUND)
        booking[0].delete()
        return Response(status=HTTP_200_OK)


class CreateSlotsForIntervalView(APIView):
    def post(self, request, *args, **kwargs):
        """Generates slots in bulk for the provided start and end interval time.

        Prevents creation of slots which conflict with the already created slots. The interval start and end need to be on the same day.

        """
        interval_start = datetime.datetime.strptime(request.data['interval_start'], "%Y-%m-%dT%H:%M:%SZ")
        interval_stop = datetime.datetime.strptime(request.data['interval_stop'], "%Y-%m-%dT%H:%M:%SZ")
        if (interval_start.day != interval_stop.day) or (interval_start.month != interval_stop.month) or (interval_start.year != interval_stop.year):
            return Response(data=ResponseMessages.INTERVAL_DAY_MISMATCH, status=HTTP_400_BAD_REQUEST)

        slot_start_time = interval_start
        slot_end_time = slot_start_time + datetime.timedelta(hours=1)
        interval_date = datetime.date(slot_start_time.year, slot_start_time.month, slot_start_time.day)
        queryset = CalenderSlot.objects.filter(belongs_to=request.user).filter(start_time__date=interval_date)
        created_slot_ids = []
        while slot_end_time <= interval_stop:
            if not queryset.filter(
                (Q(start_time__lt=slot_end_time) & Q(start_time__gte=slot_start_time)) | 
                (Q(end_time__gt=slot_start_time) & Q(end_time__lte=slot_end_time)),
                start_time__date=interval_date
            ):
                slot = CalenderSlot.objects.create(belongs_to=request.user, start_time=slot_start_time, end_time=slot_end_time)
                created_slot_ids.append(slot.id)
            slot_start_time = slot_end_time
            slot_end_time = slot_end_time + datetime.timedelta(hours=1)
        return Response(data=created_slot_ids, status=HTTP_200_OK)
