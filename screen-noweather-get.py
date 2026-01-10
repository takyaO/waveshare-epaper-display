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


def main():
    template_name = os.getenv("SCREEN_LAYOUT", "7")

    now = datetime.datetime.now()
    lang = get_active_locale()

    # =========================
    # 支配パラメータ
    # =========================
    TOTAL_ITEMS = int(os.getenv("TOTAL_ITEMS", "8"))

    TOP_Y = 30
    SCREEN_BOTTOM = 480

    EVENT_DATE_TO_DESC = 26
    TODO_DATE_TO_DESC = 24

    DIVIDER_GAP = 14
    DIVIDER_OFFSET = 4

    # =========================
    # TODO 件数（任意）
    # =========================
    try:
        todo_count = int(os.getenv("TODO_COUNT", "3"))
    except ValueError:
        todo_count = 0

    todo_count = max(0, min(todo_count, TOTAL_ITEMS - 1))
    event_count = TOTAL_ITEMS - todo_count

    # =========================
    # 高さ計算（核心）
    # =========================
    usable_height = SCREEN_BOTTOM - TOP_Y

    item_heights = (
        event_count * EVENT_DATE_TO_DESC +
        todo_count * TODO_DATE_TO_DESC
    )

    divider_height = (
        DIVIDER_OFFSET + DIVIDER_GAP if todo_count > 0 else 0
    )

    flex_height = max(
        0,
        usable_height - item_heights - divider_height
    )

    # EVENT + TODO を同一アイテムとして等間隔配置
    ITEM_GAP = flex_height // max(TOTAL_ITEMS - 1, 1)

    # =========================
    # 日付・時刻
    # =========================
    date_fmt = "%-m月 %-d日" if lang == "ja" else "%b %-d"
    time_str = now.strftime("%H:%M")

    output_dict = {
        "TIME_NOW": time_str,
        "HOUR_NOW": time_str,
        "DAY_ONE": now.strftime(date_fmt),
        "DAY_NAME": now.strftime("%A"),
    }

    # =========================
    # EVENT
    # =========================
    y = TOP_Y

    for i in range(1, event_count + 1):
        output_dict[f"EVENT_DATE_Y_{i}"] = str(y)
        output_dict[f"EVENT_DESC_Y_{i}"] = str(y + EVENT_DATE_TO_DESC)
        y += EVENT_DATE_TO_DESC + ITEM_GAP

    # 未使用 EVENT スロットを消す
    for i in range(event_count + 1, TOTAL_ITEMS + 1):
        output_dict[f"EVENT_DATE_Y_{i}"] = "0"
        output_dict[f"EVENT_DESC_Y_{i}"] = "0"
        output_dict[f"CAL_DATETIME_{i}"] = ""
        output_dict[f"CAL_DESC_{i}"] = ""

    # =========================
    # Divider / TODO
    # =========================
    if todo_count > 0:
        y += DIVIDER_OFFSET
        output_dict["DIVIDER_Y"] = str(y)
        y += DIVIDER_GAP

        for i in range(1, todo_count + 1):
            output_dict[f"TODO_DATE_Y_{i}"] = str(y)
            output_dict[f"TODO_DESC_Y_{i}"] = str(y + TODO_DATE_TO_DESC)
            y += TODO_DATE_TO_DESC + ITEM_GAP
    else:
        output_dict["DIVIDER_Y"] = "0"

    # 未使用 TODO スロットを消す
    for i in range(todo_count + 1, TOTAL_ITEMS + 1):
        output_dict[f"TODO_DATE_Y_{i}"] = "0"
        output_dict[f"TODO_DESC_Y_{i}"] = "0"
        output_dict[f"TODO_DATETIME_{i}"] = ""
        output_dict[f"TODO_DESC_{i}"] = ""

    # =========================
    # SVG 出力
    # =========================
    logging.info(
        "Updating SVG %s (TOTAL=%d EVENT=%d TODO=%d)",
        template_name, TOTAL_ITEMS, event_count, todo_count
    )

    update_svg(
        f"screen-template.{template_name}.svg",
        "screen-output-base.svg",
        output_dict
    )


if __name__ == "__main__":
    main()

