import urllib.parse

def _to_google_timestring(datetime_obj):
    return datetime_obj.strftime("%Y%m%dT%H%M%SZ")

def generate_google_calendar_link(booking_details):
    params = {
        'action': "TEMPLATE",
        'text': "Meeting with {}".format(booking_details.slot.belongs_to.username),
        'details': "{}\n\nBooking ID: {}".format(booking_details.description, booking_details.id),
        'dates': "{}/{}".format(
            _to_google_timestring(booking_details.slot.start_time), _to_google_timestring(booking_details.slot.end_time)
        )
    }
    return "https://www.google.com/calendar/render?{}".format(urllib.parse.urlencode(params))
