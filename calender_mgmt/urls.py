from django.urls import include, path

from .views import SlotDataView, SlotDetailsView

urlpatterns = [
    path('slot/<int:id>/', SlotDetailsView.as_view(), name='calender_mgmt_slot_details'),
    path('slot/', SlotDataView.as_view(), name='calender_mgmt_slot_data')
]
