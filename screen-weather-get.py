#!/usr/bin/python

import datetime
import sys
import os
import logging
import locale
import textwrap
from utility import update_svg, configure_logging, configure_locale
from weather_providers.visualcrossing import VisualCrossing

configure_locale()
configure_logging()

def get_active_locale():
    try:
        return locale.getlocale()[0][:2]
    except:
        return "en"

def format_weather_description(weather_description):
    """天候の説明を2行に分割する"""
    if len(weather_description) < 15:
        return {1: weather_description, 2: ''}

    splits = textwrap.fill(weather_description, 15, break_long_words=False,
                           max_lines=2, placeholder='...').split('\n')
    return {1: splits[0], 2: splits[1] if len(splits) > 1 else ''}

def get_weather_provider(location_lat, location_long, units):
    """Initialize the configured VisualCrossing weather provider."""
    api_key = os.getenv("VISUALCROSSING_APIKEY")
    if not api_key:
        logging.error("VISUALCROSSING_APIKEY is not configured.")
        sys.exit(1)
    return VisualCrossing(api_key, location_lat, location_long, units)

def main():
    template_name = os.getenv("SCREEN_LAYOUT", "6")
    location_lat = os.getenv("WEATHER_LATITUDE", "51.5077")
    location_long = os.getenv("WEATHER_LONGITUDE", "-0.1277")
    weather_format = os.getenv("WEATHER_FORMAT", "CELSIUS")

    units, degrees = ("metric", "°C") if weather_format == "CELSIUS" else ("imperial", "°F")

    provider = get_weather_provider(location_lat, location_long, units)
    weather = provider.get_weather()

    if not weather:
        logging.error("Unable to fetch weather. SVG will not be updated.")
        return

    # データ整形
    weather_desc = format_weather_description(weather["description"])
    now = datetime.datetime.now()
    lang = get_active_locale()

    # ロケール設定
    date_fmt = "%-m月 %-d日" if lang == "ja" else "%b %-d"
    
    # 24時間制 HH:MM に固定
    time_str = now.strftime("%H:%M")
    
    # フォントサイズ調整 (HH:MMは5文字なので通常100pxで固定されます)
    time_size = "100px"
    if len(time_str) > 6:
        time_size = f"{100 - (len(time_str)-5) * 5}px"

    output_dict = {
        'LOW_ONE': f"{round(weather['temperatureMin'])}{degrees}",
        'HIGH_ONE': f"{round(weather['temperatureMax'])}{degrees}",
        'ICON_ONE': weather["icon"],
        'WEATHER_DESC_1': weather_desc[1],
        'WEATHER_DESC_2': weather_desc[2],
        'TIME_NOW_FONT_SIZE': time_size,
        'TIME_NOW': time_str,
        'HOUR_NOW': now.strftime("%H:%M"), # AM/PMを削除
        'DAY_ONE': now.strftime(date_fmt),
        'DAY_NAME': now.strftime("%A"),
        'ALERT_MESSAGE_VISIBILITY': "hidden",
        'ALERT_MESSAGE': ""
    }

    logging.info(f"Updating SVG using template {template_name}")
    update_svg(f'screen-template.{template_name}.svg', 'screen-output-weather.svg', output_dict)

if __name__ == "__main__":
    main()
