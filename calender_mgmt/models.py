import datetime

from django.contrib.auth.models import User
from django.db import models


class CalenderSlot(models.Model):
    """Stores the calender slots available for the user to book by other people.

    """
    belongs_to = models.ForeignKey(to=User, related_name='created_slots', on_delete=models.CASCADE, help_text="""
    Stores the user the slot belongs to.
    """)
    created_at = models.DateTimeField(auto_now_add=True, help_text="""
    Django auto populates this field whenever a slot is created by a user.
    """)
    start_time = models.DateTimeField(help_text="""
    Contains the start time of the slot.
    """)
    end_time = models.DateTimeField(help_text="""
    Contains the end time of the slot.
    """)

    class Meta:
        """The default ordering is set to the descending order of when the slot was created.

        """
        ordering = ['-created_at']


class SlotBooking(models.Model):
    """Contains the booking details of the slots.

    """
    slot = models.OneToOneField(to=CalenderSlot, related_name='booking_details', on_delete=models.CASCADE, help_text="""
    References to the slot that is booked.
    """)
    booked_by = models.ForeignKey(to=User, related_name='booked_slots', on_delete=models.CASCADE, null=True, help_text="""
    Contains the user who has booked the slot. If it was booked by an anonymous user, it is None.
    """)
    booked_at = models.DateTimeField(auto_now_add=True, help_text="""
    Django automatically populates this field whenever a slot is booked.
    """)
    description = models.TextField(null=True, help_text="""
    Contains some booking data entered by the person who booked the slot.
    """)

    class Meta:
        """The default ordering is set to the descending order of when the slot was booked.

        """
        ordering = ['-booked_at']
