import datetime
import os
import logging
import emoji
import locale # 
from xml.sax.saxutils import escape

from calendar_providers.base_provider import CalendarEvent
from calendar_providers.caldav import CalDavCalendar
from calendar_providers.google import GoogleCalendar
from calendar_providers.ics import ICSCalendar
from calendar_providers.outlook import OutlookCalendar
from utility import (
    get_formatted_time,
    update_svg,
    configure_logging,
    get_formatted_date,
    configure_locale,
)

configure_locale()
configure_logging()

max_event_results = 10

google_calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
outlook_calendar_id = os.getenv("OUTLOOK_CALENDAR_ID")
caldav_calendar_urls = os.getenv("CALDAV_CALENDAR_URLS", "").split()
caldav_username = os.getenv("CALDAV_USERNAME")
caldav_password = os.getenv("CALDAV_PASSWORD")
ics_calendar_url = os.getenv("ICS_CALENDAR_URL")

def get_active_locale():
    """現在の環境の言語コード(ja, en等)を返す"""
    try:
        return locale.getlocale()[0][:2]
    except:
        return "en"

def get_datetime_formatted(event_start, event_end, is_all_day_event, start_only=False):
    lang = get_active_locale()

    if lang == "ja":
        label_today = "本日"
        label_tomorrow = "明日"
        formatter_day = "%-m月%-d日(%a)" # 1月2日(金)
    else:
        label_today = "Today"
        label_tomorrow = "Tomorrow"
        formatter_day = "%a, %b %-d"   # Fri, Jan 2

    now_dt = datetime.datetime.now().astimezone()
    today = now_dt.date()
    tomorrow = today + datetime.timedelta(days=1)

    if is_all_day_event or (isinstance(event_start, datetime.date) and not isinstance(event_start, datetime.datetime)):
        start = datetime.datetime.combine(event_start, datetime.time.min)
        start_day_str = start.strftime(formatter_day)
        return start_day_str
    
    # 通常イベント
    start_dt = event_start.astimezone()
    end_dt = event_end.astimezone()

    if start_dt.date() == today:
        day_str = label_today
    elif start_dt.date() == tomorrow:
        day_str = label_tomorrow
    else:
        day_str = start_dt.strftime(formatter_day)

    start_time_str = start_dt.strftime("%H:%M")
    end_time_str = end_dt.strftime("%H:%M")

    if start_only:
        return f"{day_str} {start_time_str}"
    else:
        return f"{day_str} {start_time_str} - {end_time_str}"

def get_formatted_calendar_events(fetched_events: list[CalendarEvent]) -> dict:
    formatted_events = {}
    event_count = len(fetched_events)

    for index in range(max_event_results):
        event_label_id = str(index + 1)
        if index < event_count:
            event = fetched_events[index]
            
            dt_str_full = get_datetime_formatted(event.start, event.end, event.all_day_event)
            dt_str_start = get_datetime_formatted(event.start, event.end, event.all_day_event, start_only=True)

            formatted_events['CAL_DATETIME_' + event_label_id] = dt_str_full
            formatted_events['CAL_DATETIME_START_' + event_label_id] = dt_str_start
            formatted_events['CAL_DESC_' + event_label_id] = event.summary
        else:
            formatted_events['CAL_DATETIME_' + event_label_id] = ""
            formatted_events['CAL_DATETIME_START_' + event_label_id] = ""
            formatted_events['CAL_DESC_' + event_label_id] = ""

    return formatted_events

def main():
    output_svg_filename = "screen-output-weather.svg"
    
    now = datetime.datetime.now().astimezone()
    
    if os.getenv("CALENDAR_INCLUDE_PAST_EVENTS_FOR_TODAY", "0") == "1":
        today_start_time = datetime.datetime.combine(now.date(), datetime.time.min).astimezone(now.tzinfo)
    else:
        today_start_time = now

    oneyearlater_iso = now + datetime.timedelta(days=365)

    if outlook_calendar_id:
        provider = OutlookCalendar(outlook_calendar_id, max_event_results, today_start_time, oneyearlater_iso)
    elif caldav_calendar_urls:
        provider = CalDavCalendar(caldav_calendar_urls, max_event_results, today_start_time, oneyearlater_iso, caldav_username, caldav_password)
    elif ics_calendar_url:
        provider = ICSCalendar(ics_calendar_url, max_event_results, today_start_time, oneyearlater_iso)
    else:
        provider = GoogleCalendar(google_calendar_id, max_event_results, today_start_time, oneyearlater_iso)

    calendar_events = provider.get_calendar_events()
    
    filtered_events = []
    for e in calendar_events:
        if isinstance(e.end, datetime.datetime):
            end_dt = e.end.astimezone()
        else:
            end_dt = datetime.datetime.combine(e.end, datetime.time.max).astimezone(now.tzinfo)
        
        if end_dt > now:
            filtered_events.append(e)

    output_dict = get_formatted_calendar_events(filtered_events)

    for key, value in output_dict.items():
        escaped_val = escape(value)
        output_dict[key] = emoji.replace_emoji(
            escaped_val,
            replace=lambda chars, _: f'<tspan style="font-family:emoji">{chars}</tspan>'
        )

    logging.info("Updating SVG with %d events", len(filtered_events))
    update_svg(output_svg_filename, output_svg_filename, output_dict)

if __name__ == "__main__":
    main()
