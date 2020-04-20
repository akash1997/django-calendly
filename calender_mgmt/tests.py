import datetime

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from rest_framework.authtoken.models import Token
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
)
from rest_framework.test import APITestCase

from .constants import ResponseMessages
from .functions import generate_google_calendar_link
from .models import CalenderSlot, SlotBooking


class CreateCalendarSlotTestCase(APITestCase):
    def setUp(self):
        self.email = 'test@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)

    def test_create_slot_unauthenticated(self):
        url = reverse('calender_mgmt:slot_data')
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        data = {'start_time': start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.client.credentials()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(CalenderSlot.objects.count(), 0)

    def test_create_slot_wrong_key(self):
        url = reverse('calender_mgmt:slot_data')
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        data = {'start_tim': start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.MISSING_KEY.format('start_time'))
        self.assertEqual(CalenderSlot.objects.count(), 0)

    def test_create_slot_wrong_datetime_format(self):
        url = reverse('calender_mgmt:slot_data')
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        data = {'start_time': start_time.strftime("%Y-%m-%d%H:%M:%S")}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.INVALID_DATA)
        self.assertEqual(CalenderSlot.objects.count(), 0)

    def test_create_slot_in_the_past(self):
        url = reverse('calender_mgmt:slot_data')
        start_time = datetime.datetime.now() + datetime.timedelta(days=-1)
        data = {'start_time': start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.CREATE_FUTURE_SLOTS)
        self.assertEqual(CalenderSlot.objects.count(), 0)

    def test_create_conflicting_slot(self):
        existing_start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=30)
        existing_end_time = existing_start_time + datetime.timedelta(hours=1)
        CalenderSlot.objects.create(
            belongs_to=self.user, start_time=existing_start_time, end_time=existing_end_time
        )
        url = reverse('calender_mgmt:slot_data')
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        data = {'start_time': start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.CONFLICTING_SLOT.format(existing_start_time, existing_end_time))
        self.assertEqual(CalenderSlot.objects.count(), 1)

    def test_create_correct_slot(self):
        url = reverse('calender_mgmt:slot_data')
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=1)
        data = {'start_time': start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(CalenderSlot.objects.count(), 1)


class GetCreatedCalendarSlotsTestCase(APITestCase):
    def setUp(self):
        self.url = reverse('calender_mgmt:slot_data')
        self.email = 'test1@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)
        self.start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        self.end_time = self.start_time + datetime.timedelta(hours=1)
        self.slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=self.start_time, end_time=self.end_time
        )
        self.other_user = User.objects.create_user(
            username='test2@mail.com', email='test2@mail.com', password='password'
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=45)
        end_time = start_time + datetime.timedelta(hours=1)
        CalenderSlot.objects.create(belongs_to=self.other_user, start_time=start_time, end_time=end_time)

    def test_get_slots_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_get_slots_unbooked(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        slot_data = {'id': self.slot.id, 'start_time': str(self.slot.start_time), 'end_time': str(self.slot.end_time), 'is_booked': False}
        self.assertEqual(response.data[0], slot_data)

    def test_get_slots_booked(self):
        SlotBooking.objects.create(slot=self.slot)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        slot_data = {'id': self.slot.id, 'start_time': str(self.slot.start_time), 'end_time': str(self.slot.end_time), 'is_booked': True}
        self.assertEqual(response.data[0], slot_data)


class GetCalendarSlotDetailsTestCase(APITestCase):
    def setUp(self):
        self.email = 'test1@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)
        self.start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        self.end_time = self.start_time + datetime.timedelta(hours=1)
        self.slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=self.start_time, end_time=self.end_time
        )
        self.other_user = User.objects.create_user(
            username='test2@mail.com', email='test2@mail.com', password='password'
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=45)
        end_time = start_time + datetime.timedelta(hours=1)
        self.other_user_slot = CalenderSlot.objects.create(
            belongs_to=self.other_user, start_time=start_time, end_time=end_time
        )

    def test_get_slots_unauthenticated(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.slot.id})
        self.client.credentials()
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_incorrect_slot_details(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': 3234})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_NOT_FOUND)

    def test_other_user_slot_details(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.other_user_slot.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_NOT_FOUND)

    def test_my_slot_details_unbooked(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.slot.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        slot_data = {
            'id': self.slot.id,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'is_booked': False
        }
        self.assertEqual(response.data, slot_data)

    def test_my_slot_details_booked_anonymous_user(self):
        booking = SlotBooking.objects.create(slot=self.slot, description="Important")
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.slot.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        slot_data = {
            'id': self.slot.id,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'is_booked': True,
            'booking_id': booking.id,
            'booked_by': "Anonymous User",
            'booked_at': str(booking.booked_at),
            'description': "Important"
        }
        self.assertEqual(response.data, slot_data)

    def test_my_slot_details_booked_registered_user(self):
        booking = SlotBooking.objects.create(
            slot=self.slot, booked_by=self.other_user, description="Important"
        )
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.slot.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        slot_data = {
            'id': self.slot.id,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'is_booked': True,
            'booking_id': booking.id,
            'booked_by': self.other_user.username,
            'booked_at': str(booking.booked_at),
            'description': "Important"
        }
        self.assertEqual(response.data, slot_data)


class DeleteCalendarSlotTestCase(APITestCase):
    def setUp(self):
        self.email = 'test1@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)
        self.start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        self.end_time = self.start_time + datetime.timedelta(hours=1)
        self.slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=self.start_time, end_time=self.end_time
        )
        self.other_user = User.objects.create_user(
            username='test2@mail.com', email='test2@mail.com', password='password'
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=45)
        end_time = start_time + datetime.timedelta(hours=1)
        self.other_user_slot = CalenderSlot.objects.create(
            belongs_to=self.other_user, start_time=start_time, end_time=end_time
        )

    def test_delete_slot_unauthenticated(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.slot.id})
        self.client.credentials()
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(CalenderSlot.objects.count(), 2)

    def test_delete_nonexistent_slot(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': 12346})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_NOT_FOUND)
        self.assertEqual(CalenderSlot.objects.count(), 2)

    def test_delete_other_user_slot(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.other_user_slot.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_NOT_FOUND)
        self.assertEqual(CalenderSlot.objects.count(), 2)

    def test_delete_current_user_slot(self):
        url = reverse('calender_mgmt:slot_details', kwargs={'id': self.slot.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(CalenderSlot.objects.count(), 1)
        self.assertEqual(CalenderSlot.objects.filter(belongs_to=self.user).count(), 0)


class GetAvailableCalendarSlotToBookTestCase(APITestCase):
    def setUp(self):
        self.email = 'test1@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)
        start_time = datetime.datetime.now() + datetime.timedelta(days=-1)
        end_time = start_time + datetime.timedelta(hours=1)
        CalenderSlot.objects.create(belongs_to=self.user, start_time=start_time, end_time=end_time)
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=1)
        self.future_slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=start_time, end_time=end_time
        )
        self.other_user = User.objects.create_user(
            username='test2@mail.com', email='test2@mail.com', password='password'
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=45)
        end_time = start_time + datetime.timedelta(hours=1)
        self.other_user_slot = CalenderSlot.objects.create(
            belongs_to=self.other_user, start_time=start_time, end_time=end_time
        )

    def test_get_booking_slots_unauthenticated(self):
        url = reverse('calender_mgmt:available_slots', kwargs={'user_id': self.user.id})
        self.client.credentials()
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        available_slots_data = [{
            'id': self.future_slot.id,
            'start_time': str(self.future_slot.start_time),
            'end_time': str(self.future_slot.end_time)
        }]
        self.assertEqual(response.data, available_slots_data)

    def test_get_booking_slots_authenticated(self):
        url = reverse('calender_mgmt:available_slots', kwargs={'user_id': self.user.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        available_slots_data = [{
            'id': self.future_slot.id,
            'start_time': str(self.future_slot.start_time),
            'end_time': str(self.future_slot.end_time)
        }]
        self.assertEqual(response.data, available_slots_data)

    def test_get_booking_slots_incorrect_user_id(self):
        url = reverse('calender_mgmt:available_slots', kwargs={'user_id': 5767})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.USER_NOT_FOUND)


class BookCalendarSlotTestCase(APITestCase):
    def setUp(self):
        self.email = 'test1@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=-1)
        end_time = start_time + datetime.timedelta(hours=1)
        self.past_slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=start_time, end_time=end_time
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=1)
        self.future_slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=start_time, end_time=end_time
        )
        self.other_user = User.objects.create_user(
            username='test2@mail.com', email='test2@mail.com', password='password'
        )
        token = Token.objects.create(user=self.other_user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)
        start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=45)
        end_time = start_time + datetime.timedelta(hours=1)
        self.other_user_slot = CalenderSlot.objects.create(
            belongs_to=self.other_user, start_time=start_time, end_time=end_time
        )

    def test_book_slot_unauthenticated(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.future_slot.id})
        self.client.credentials()
        data = {'description': "Something important"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        booking = SlotBooking.objects.get(
            slot=self.future_slot, booked_by=None, description="Something important"
        )
        expected_response_data = {
            "id": booking.id,
            "add_to_google_calendar": generate_google_calendar_link(booking)
        }
        self.assertEqual(response.data, expected_response_data)
        self.assertEqual(SlotBooking.objects.count(), 1)

    def test_book_slot_authenticated(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.future_slot.id})
        data = {'description': "Something important"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        booking = SlotBooking.objects.get(
            slot=self.future_slot, booked_by=self.other_user, description="Something important"
        )
        expected_response_data = {
            "id": booking.id,
            "add_to_google_calendar": generate_google_calendar_link(booking)
        }
        self.assertEqual(response.data, expected_response_data)
        self.assertEqual(SlotBooking.objects.count(), 1)

    def test_book_incorrect_slot(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': 5473})
        data = {'description': "Something important"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_NOT_FOUND)
        self.assertEqual(SlotBooking.objects.count(), 0)

    def test_book_already_booked_slot(self):
        SlotBooking.objects.create(slot=self.future_slot, booked_by=None, description="Something important!")
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.future_slot.id})
        data = {'description': "Something important"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_ALREADY_BOOKED)
        self.assertEqual(SlotBooking.objects.count(), 1)

    def test_book_past_slot(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.past_slot.id})
        data = {'description': "Something important"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.CALENDER_SLOT_EXPIRED)
        self.assertEqual(SlotBooking.objects.count(), 0)

    def test_book_slot_incorrect_key(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.future_slot.id})
        data = {'descriptio': "Something important"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ResponseMessages.MISSING_KEY.format('description'))
        self.assertEqual(SlotBooking.objects.count(), 0)


class CancelBookedSlotTestCase(APITestCase):
    def setUp(self):
        self.email = 'test1@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=-1)
        end_time = start_time + datetime.timedelta(hours=1)
        self.past_slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=start_time, end_time=end_time
        )
        start_time = datetime.datetime.now() + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=1)
        self.future_slot = CalenderSlot.objects.create(
            belongs_to=self.user, start_time=start_time, end_time=end_time
        )
        self.other_user = User.objects.create_user(
            username='test2@mail.com', email='test2@mail.com', password='password'
        )
        token = Token.objects.create(user=self.other_user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)
        start_time = datetime.datetime.now() + datetime.timedelta(days=1, minutes=45)
        end_time = start_time + datetime.timedelta(hours=1)
        self.other_user_slot = CalenderSlot.objects.create(
            belongs_to=self.other_user, start_time=start_time, end_time=end_time
        )
        SlotBooking.objects.create(
            slot=self.future_slot, description="Something important!", booked_by=None
        )
        SlotBooking.objects.create(
            slot=self.other_user_slot, description="Something more important", booked_by=self.user
        )

    def test_cancel_booking_unauthenticated(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.future_slot.id})
        self.client.credentials()
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, ResponseMessages.REGISTERATION_REQUIRED)
        self.assertEqual(SlotBooking.objects.count(), 2)

    def test_cancel_booking_of_incorrect_slot(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': 9425})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.BOOKING_NOT_FOUND)
        self.assertEqual(SlotBooking.objects.count(), 2)

    def test_cancel_booking_of_other_user(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.future_slot.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, ResponseMessages.BOOKING_NOT_FOUND)
        self.assertEqual(SlotBooking.objects.count(), 2)

    def test_cancel_booking_by_person_who_booked(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.other_user_slot.id})
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(SlotBooking.objects.count(), 1)
        self.assertFalse(SlotBooking.objects.filter(slot=self.other_user_slot).exists())

    def test_cancel_booking_by_slot_owner(self):
        url = reverse('calender_mgmt:book_slot', kwargs={'id': self.other_user_slot.id})
        token = Token.objects.create(user=self.user).key
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(SlotBooking.objects.count(), 1)
        self.assertFalse(SlotBooking.objects.filter(slot=self.other_user_slot).exists())


class CreateSlotsForIntervalTestCase(APITestCase):
    def setUp(self):
        self.url = reverse('calender_mgmt:slot_interval')
        self.email = 'test@mail.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.password
        )
        token = Token.objects.create(user=self.user).key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer "+ token)

    def test_create_interval_slots_unauthenticated(self):
        self.client.credentials()
        interval_start = datetime.datetime.now() + datetime.timedelta(days=1)
        interval_stop = interval_start + datetime.timedelta(hours=9)
        data = {
            "interval_start": interval_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "interval_stop": interval_stop.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(CalenderSlot.objects.count(), 0)

    def test_create_interval_skip_creating_conflicting_slots(self):
        interval_start = datetime.datetime.now() + datetime.timedelta(days=1)
        interval_stop = interval_start + datetime.timedelta(hours=2)
        existing_slot_start_time = interval_start + datetime.timedelta(minutes=30)
        existing_slot_end_time = existing_slot_start_time + datetime.timedelta(hours=1)
        CalenderSlot.objects.create(
            belongs_to=self.user, start_time=existing_slot_start_time, end_time=existing_slot_end_time
        )
        data = {
            "interval_start": interval_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "interval_stop": interval_stop.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.assertEqual(CalenderSlot.objects.count(), 1)

    def test_create_interval_slots(self):
        interval_start = datetime.datetime.now() + datetime.timedelta(days=1)
        interval_stop = interval_start + datetime.timedelta(hours=5)
        data = {
            "interval_start": interval_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "interval_stop": interval_stop.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(CalenderSlot.objects.count(), 5)
