#!/usr/bin/python

import datetime
import sys
import os
import logging
import locale
import textwrap
import html
from utility import update_svg, configure_logging, configure_locale
# 各プロバイダのインポート（そのまま）
from weather_providers import (climacell, openweathermap, metofficedatahub, 
                               metno, meteireann, accuweather, visualcrossing, 
                               weathergov, smhi)
from alert_providers import metofficerssfeed, weathergovalerts
from alert_providers import meteireann as meteireannalertprovider

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
    """環境変数から適切な気象プロバイダを初期化して返す"""
    configs = {
        "visualcrossing": os.getenv("VISUALCROSSING_APIKEY"),
        "met_eireann": os.getenv("WEATHER_MET_EIREANN"),
        "weathergov": os.getenv("WEATHERGOV_SELF_IDENTIFICATION"),
        "metno": os.getenv("METNO_SELF_IDENTIFICATION"),
        "accuweather": os.getenv("ACCUWEATHER_APIKEY"),
        "metoffice": os.getenv("METOFFICEDATAHUB_API_KEY"),
        "openweathermap": os.getenv("OPENWEATHERMAP_APIKEY"),
        "climacell": os.getenv("CLIMACELL_APIKEY"),
        "smhi": os.getenv("SMHI_SELF_IDENTIFICATION")
    }

    if not any(configs.values()):
        logging.error("No weather provider configured.")
        sys.exit(1)

    # 優先順位に従ってプロバイダを返却
    if configs["visualcrossing"]:
        return visualcrossing.VisualCrossing(configs["visualcrossing"], location_lat, location_long, units)
    if configs["met_eireann"]:
        return meteireann.MetEireann(location_lat, location_long, units)
    if configs["weathergov"]:
        return weathergov.WeatherGov(configs["weathergov"], location_lat, location_long, units)
    if configs["metno"]:
        return metno.MetNo(configs["metno"], location_lat, location_long, units)
    if configs["accuweather"]:
        return accuweather.AccuWeather(configs["accuweather"], location_lat, location_long, os.getenv("ACCUWEATHER_LOCATIONKEY"), units)
    if configs["metoffice"]:
        return metofficedatahub.MetOffice(configs["metoffice"], location_lat, location_long, units)
    if configs["openweathermap"]:
        return openweathermap.OpenWeatherMap(configs["openweathermap"], location_lat, location_long, units)
    if configs["climacell"]:
        return climacell.Climacell(configs["climacell"], location_lat, location_long, units)
    if configs["smhi"]:
        return smhi.SMHI(configs["smhi"], location_lat, location_long, units)

def get_alert_message(location_lat, location_long):
    alert_metoffice = os.getenv("ALERT_METOFFICE_FEED_URL")
    alert_weathergov = os.getenv("ALERT_WEATHERGOV_SELF_IDENTIFICATION")
    alert_meteireann = os.getenv("ALERT_MET_EIREANN_FEED_URL")

    if alert_weathergov:
        return weathergovalerts.WeatherGovAlerts(location_lat, location_long, alert_weathergov).get_alert()
    if alert_metoffice:
        return metofficerssfeed.MetOfficeRssFeed(alert_metoffice).get_alert()
    if alert_meteireann:
        return meteireannalertprovider.MetEireannAlertProvider(alert_meteireann).get_alert()
    return ""

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
    alert_msg = html.escape(get_alert_message(location_lat, location_long))
    
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
        'ALERT_MESSAGE_VISIBILITY': "visible" if alert_msg else "hidden",
        'ALERT_MESSAGE': alert_msg
    }

    logging.info(f"Updating SVG using template {template_name}")
    update_svg(f'screen-template.{template_name}.svg', 'screen-output-weather.svg', output_dict)

if __name__ == "__main__":
    main()
