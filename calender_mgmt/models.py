import datetime

from django.contrib.auth.models import User
from django.db import models


class CalenderSlot(models.Model):
    belongs_to = models.ForeignKey(to=User, related_name='created_slots', on_delete=models.CASCADE)
    slot_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def save(self, *args, **kwargs):
        self.end_time = self.start_time + datetime.timedelta(hours=1)
        super().save(*args, **kwargs)


class SlotBooking(models.Model):
    slot = models.OneToOneField(to=CalenderSlot, related_name='booking_details', on_delete=models.CASCADE)
    booked_by = models.ForeignKey(to=User, related_name='booked_slots', on_delete=models.CASCADE, null=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True)
