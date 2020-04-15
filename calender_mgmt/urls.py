from django.urls import include, path

from .views import SlotDataView

urlpatterns = [
    path('slot/', SlotDataView.as_view(), name='calender_mgmt_slot_data')
]
