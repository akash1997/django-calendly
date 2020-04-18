from django.urls import include, path

from .views import BookSlotView, CreateSlotsForIntervalView, GetAvailableSlots, SlotDataView, SlotDetailsView

urlpatterns = [
    path('book/slot/<int:id>/', BookSlotView.as_view(), name='book_slot'),
    path('book/slots/', GetAvailableSlots.as_view(), name='available_slots'),
    path('slot/<int:id>/', SlotDetailsView.as_view(), name='slot_details'),
    path('slot/', SlotDataView.as_view(), name='slot_data'),
    path('slots/interval/', CreateSlotsForIntervalView.as_view(), name='slot_interval')
]
