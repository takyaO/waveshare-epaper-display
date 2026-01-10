import caldav
import logging
from .base_provider import BaseCalendarProvider, CalendarEvent
from datetime import datetime, date, time, timezone, timedelta


class CalDavCalendar(BaseCalendarProvider):

    def __init__(self, calendar_urls, max_event_results, from_date, to_date, username=None, password=None):
        self.calendar_urls = calendar_urls
        self.max_event_results = max_event_results
        self.username = username
        self.password = password
        self.from_date = from_date
        self.to_date = to_date

    def get_calendar_events(self):

        events_data = []
        calendar_events = []

        # ★ 最初のURLを base URL として使う（重要）
        base_url = self.calendar_urls[0]

        with caldav.DAVClient(
            url=base_url,
            username=self.username,
            password=self.password
        ) as client:

            for url in self.calendar_urls:
                logging.info(f"Fetching CalDAV calendar: {url}")

                calendar = caldav.Calendar(client, url=url)

                results = calendar.date_search(
                    start=self.from_date,
                    end=self.to_date,
                    expand=True
                )

                for result in results:
                    for component in result.icalendar_instance.subcomponents:
                        if 'DTSTART' in component:
                            events_data.append(component)

        def normalize_dt(dt):
            if isinstance(dt, datetime):
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            return datetime.combine(dt, time.min, tzinfo=timezone.utc)

        events_data.sort(key=lambda x: normalize_dt(x['DTSTART'].dt))

        for event in events_data[:self.max_event_results]:
            start = event['DTSTART'].dt

            if 'DTEND' in event:
                end = event['DTEND'].dt
            elif 'DURATION' in event:
                end = start + event['DURATION'].dt
            else:
                end = start

            all_day = isinstance(start, date) and not isinstance(start, datetime)
            if all_day:
                end = end - timedelta(days=1)

            summary = str(event.get('SUMMARY', ''))

            location = ""
            if 'LOCATION' in event:
                location = str(event.get('LOCATION'))

            calendar_events.append(
                CalendarEvent(
                    summary,
                    start,
                    end,
                    all_day,
                    location
                )
            )

        return calendar_events

    def get_calendar_todos(self):
        """
        CalDAV から VTODO を取得する
        """
        todos = []

        base_url = self.calendar_urls[0]

        with caldav.DAVClient(
            url=base_url,
            username=self.username,
            password=self.password
        ) as client:

            for url in self.calendar_urls:
                logging.info(f"Fetching CalDAV todos: {url}")
                calendar = caldav.Calendar(client, url=url)

                try:
                    results = calendar.search(
                        event=False,
                        todo=True,
                        include_completed=True,
                    )
                except Exception as e:
                    logging.warning("Failed to fetch VTODOs: %s", e)
                    continue

                for result in results:
                    vobj = result.vobject_instance
                    if not hasattr(vobj, "vtodo"):
                        continue

                    vtodo = vobj.vtodo

                    summary = str(vtodo.summary.value) if hasattr(vtodo, "summary") else ""

                    due = None
                    if hasattr(vtodo, "due"):
                        due = vtodo.due.value
                        if isinstance(due, date) and not isinstance(due, datetime):
                            due = datetime.combine(due, time.max)

                    completed = (
                        hasattr(vtodo, "completed")
                        or (
                            hasattr(vtodo, "status")
                            and str(vtodo.status.value).upper() == "COMPLETED"
                        )
                    )

                    todos.append(
                        type(
                            "Todo",
                            (),
                            {
                                "summary": summary,
                                "due": due,
                                "completed": completed,
                            },
                        )()
                    )

        return todos

