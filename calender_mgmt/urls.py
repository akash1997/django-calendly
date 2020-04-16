from django.urls import include, path

from .views import GetAvailableSlots, SlotDataView, SlotDetailsView

urlpatterns = [
    path('book/slots/', GetAvailableSlots.as_view(), name='calender_mgmt_available_slots'),
    path('slot/<int:id>/', SlotDetailsView.as_view(), name='calender_mgmt_slot_details'),
    path('slot/', SlotDataView.as_view(), name='calender_mgmt_slot_data')
]
