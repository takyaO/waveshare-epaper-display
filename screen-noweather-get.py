#!/usr/bin/python

import datetime
import os
import logging
import locale

from utility import update_svg, configure_logging, configure_locale

configure_locale()
configure_logging()


def get_active_locale():
    try:
        return locale.getlocale()[0][:2]
    except Exception:
        return "en"


def calc_event_positions(event_limit, top_y, date_to_desc, block_gap):
    y = top_y
    pos = []
    for _ in range(event_limit):
        pos.append((y, y + date_to_desc))
        y += date_to_desc + block_gap
    return pos, y


def main():
    template_name = os.getenv("SCREEN_LAYOUT", "7")

    now = datetime.datetime.now()
    lang = get_active_locale()

    # =========================
    # レイアウト定数
    # =========================
    BASE_EVENT = 4
    MAX_EVENT = 6
    MAX_TODO = 3

    EVENT_DATE_TO_DESC = 26
    EVENT_BLOCK_GAP = 24

    TODO_DATE_TO_DESC = 24
    TODO_BLOCK_GAP = 16

    DIVIDER_GAP = 14
    DIVIDER_OFFSET = 4

    TOP_Y = 30
    SCREEN_BOTTOM = 480

    # =========================
    # TODO 件数
    # =========================
    try:
        todo_count = int(os.getenv("TODO_COUNT", "3"))
    except ValueError:
        todo_count = 3

    todo_count = max(0, min(todo_count, MAX_TODO))

    # =========================
    # EVENT 件数を高さから決定
    # =========================
    EVENT_MIN_HEIGHT = EVENT_DATE_TO_DESC + EVENT_BLOCK_GAP

    reserved = 0
    if todo_count > 0:
        reserved = (
            DIVIDER_OFFSET
            + DIVIDER_GAP
            + todo_count * (TODO_DATE_TO_DESC + TODO_BLOCK_GAP)
        )

    available = SCREEN_BOTTOM - TOP_Y - reserved
    event_fit = available // EVENT_MIN_HEIGHT

    event_limit = min(max(event_fit, BASE_EVENT), MAX_EVENT)

    # =========================
    # 日付・時刻
    # =========================
    date_fmt = "%-m月 %-d日" if lang == "ja" else "%b %-d"
    time_str = now.strftime("%H:%M")

    time_size = "100px"
    if len(time_str) > 6:
        time_size = f"{100 - (len(time_str) - 5) * 5}px"

    output_dict = {
        'TIME_NOW_FONT_SIZE': time_size,
        'TIME_NOW': time_str,
        'HOUR_NOW': now.strftime("%H:%M"),
        'DAY_ONE': now.strftime(date_fmt),
        'DAY_NAME': now.strftime("%A"),
    }

    # =========================
    # EVENT 配置（余白再配分込み）
    # =========================
    event_pos, y = calc_event_positions(
        event_limit, TOP_Y, EVENT_DATE_TO_DESC, EVENT_BLOCK_GAP
    )

    remaining = SCREEN_BOTTOM - y - reserved

    if remaining > 20 and event_limit <= BASE_EVENT:
        EVENT_BLOCK_GAP += remaining // event_limit
        event_pos, y = calc_event_positions(
            event_limit, TOP_Y, EVENT_DATE_TO_DESC, EVENT_BLOCK_GAP
        )

    for i, (dy, sy) in enumerate(event_pos, start=1):
        output_dict[f"EVENT_DATE_Y_{i}"] = str(dy)
        output_dict[f"EVENT_DESC_Y_{i}"] = str(sy)

    for i in range(event_limit + 1, MAX_EVENT + 1):
        output_dict[f"EVENT_DATE_Y_{i}"] = "0"
        output_dict[f"EVENT_DESC_Y_{i}"] = "0"
        output_dict[f"CAL_DATETIME_{i}"] = ""
        output_dict[f"CAL_DESC_{i}"] = ""

    # =========================
    # Divider / TODO（1回だけ）
    # =========================
    if todo_count == 0:
        output_dict["DIVIDER_Y"] = "0"
    else:
        divider_y = y + DIVIDER_OFFSET
        output_dict["DIVIDER_Y"] = str(divider_y)
        y = divider_y + DIVIDER_GAP

        for i in range(1, todo_count + 1):
            output_dict[f"TODO_DATE_Y_{i}"] = str(y)
            output_dict[f"TODO_DESC_Y_{i}"] = str(y + TODO_DATE_TO_DESC)
            y += TODO_DATE_TO_DESC + TODO_BLOCK_GAP

    for i in range(todo_count + 1, MAX_TODO + 1):
        output_dict[f"TODO_DATE_Y_{i}"] = "0"
        output_dict[f"TODO_DESC_Y_{i}"] = "0"
        output_dict[f"TODO_DATETIME_{i}"] = ""
        output_dict[f"TODO_DESC_{i}"] = ""

    # =========================
    # SVG 出力
    # =========================
    logging.info(
        "Updating SVG %s (EVENT=%d TODO=%d end_y=%d)",
        template_name, event_limit, todo_count, y
    )

    update_svg(
        f"screen-template.{template_name}.svg",
        "screen-output-base.svg",
        output_dict
    )


if __name__ == "__main__":
    main()

