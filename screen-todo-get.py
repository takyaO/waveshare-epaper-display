#!/usr/bin/python

import datetime
import os
import logging
import emoji
import locale
from xml.sax.saxutils import escape
from datetime import timezone

from calendar_providers.caldav import CalDavCalendar
from utility import (
    update_svg,
    configure_logging,
    configure_locale,
)

configure_locale()
configure_logging()

max_todo_results = 10

# === CalDAV only ===
caldav_calendar_urls = os.getenv("CALDAV_CALENDAR_URLS", "").split()
caldav_username = os.getenv("CALDAV_USERNAME")
caldav_password = os.getenv("CALDAV_PASSWORD")


def get_active_locale():
    try:
        return locale.getlocale()[0][:2]
    except Exception:
        return "en"


def format_due_date(due: datetime.datetime | None):
    """VTODO の due を人間向け表記に変換"""
    if not due:
        return ""

    lang = get_active_locale()
    now = datetime.datetime.now().astimezone()
    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)

    due = due.astimezone() if isinstance(due, datetime.datetime) else due

    if due.date() == today:
        return "今日" if lang == "ja" else "Today"
    if due.date() == tomorrow:
        return "明日" if lang == "ja" else "Tomorrow"

    fmt = "%-m/%-d" if lang == "ja" else "%b %-d"
    return due.strftime(fmt)


def get_formatted_todos(todos: list) -> dict:
    output = {}

    for index in range(max_todo_results):
        label_id = str(index + 1)

        if index < len(todos):
            todo = todos[index]

            output[f"TODO_DATETIME_{label_id}"] = format_due_date(todo.due)
            output[f"TODO_DESC_{label_id}"] = todo.summary
        else:
            output[f"TODO_DATETIME_{label_id}"] = ""
            output[f"TODO_DESC_{label_id}"] = ""

    return output

def main():
    output_svg_filename = "screen-output-weather.svg"

    provider = CalDavCalendar(
        caldav_calendar_urls,
        max_todo_results,
        None,
        None,
        caldav_username,
        caldav_password,
    )

    # === VTODO only ===
    todos = provider.get_calendar_todos()

    # 未完了のみ + 期限順
    todos = [
        t for t in todos if not t.completed
    ]

    def normalize_due(due):
        if due is None:
            return datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
        if isinstance(due, datetime.datetime):
            return due if due.tzinfo else due.replace(tzinfo=datetime.timezone.utc)
        return datetime.datetime.combine(
            due, datetime.time.max, tzinfo=datetime.timezone.utc
        )
    todos.sort(key=lambda t: normalize_due(t.due))

    output_dict = get_formatted_todos(todos)

    for key, value in output_dict.items():
        escaped_val = escape(value)
        output_dict[key] = emoji.replace_emoji(
            escaped_val,
            replace=lambda chars, _: f'<tspan style="font-family:emoji">{chars}</tspan>'
        )

    logging.info("Updating SVG with %d todos", len(todos))
    update_svg(output_svg_filename, output_svg_filename, output_dict)


if __name__ == "__main__":
    main()
