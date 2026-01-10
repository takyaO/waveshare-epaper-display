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
    template_name = os.getenv("SCREEN_LAYOUT", "6")

    now = datetime.datetime.now()
    lang = get_active_locale()

    # 日付フォーマット
    date_fmt = "%-m月 %-d日" if lang == "ja" else "%b %-d"

    # 24時間制 HH:MM
    time_str = now.strftime("%H:%M")

    # フォントサイズ調整（将来の拡張用に残す）
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

    logging.info(f"Updating SVG using template {template_name}")
    update_svg(
        f"screen-template.{template_name}.svg",
        "screen-output-weather.svg",
        output_dict
    )


if __name__ == "__main__":
    main()
