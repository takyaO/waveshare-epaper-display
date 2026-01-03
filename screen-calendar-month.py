import datetime
import calendar
import os
from utility import update_svg, configure_locale, configure_logging
import locale
import babel
import logging
from collections import deque
import drawsvg as draw

configure_logging()
configure_locale()

def get_safe_babel_locale():
    """環境変数やシステム設定から安全にBabelロケールを取得する"""
    # 1. 環境変数を直接チェック
    env_lang = os.getenv("LANG", "en_US.UTF-8").split('.')[0]
    
    try:
        return babel.Locale.parse(env_lang)
    except (babel.core.UnknownLocaleError, ValueError):
        try:
            # 2. localeモジュールから試行
            loc = locale.getlocale()[0]
            if loc:
                return babel.Locale.parse(loc)
        except:
            pass
    
    # 3. 最終手段：デフォルトを英語にする
    logging.warning("Fallback to default locale 'en_US'")
    return babel.Locale.parse("en_US")

# エラーが出ていた箇所をこの関数に置き換え
babel_locale = get_safe_babel_locale()
logging.debug(f"Using Babel locale: {babel_locale}")

def main():
    logging.info("Generating SVG for calendar month")
    calendar.setfirstweekday(babel_locale.first_week_day)

    # タイムゾーンを考慮した「今日」の取得（昨日が混ざるバグを防止）
    now = datetime.datetime.now().astimezone()
    current_year, current_month, current_day = now.year, now.month, now.day
    cal = calendar.monthcalendar(current_year, current_month)

    # 元のサイズ設定に戻しました
    cell_width = 40
    cell_height = 30
    font_size_val = 26 # お好みのサイズに調整してください

    dwg_width = cell_width * 7
    dwg_height = cell_height * (len(cal) + 1)
    
    dwg = draw.Drawing(width=dwg_width, height=dwg_height, id='month-cal-inner')

    day_abbr = deque(list(calendar.day_abbr))
    day_abbr.rotate(-calendar.firstweekday())

    # 曜日ヘッダー（元の座標 y=20）
    for i, day in enumerate(day_abbr):
        dwg.append(draw.Text(day[:2], font_size=font_size_val * 0.6, 
                             x=i*cell_width + 20, y=20, 
                             text_anchor='middle', fill='black'))

    # 日付（元の座標計算 y=(i+2)*cell_height - 10）
    for i, week in enumerate(cal):
        for j, day in enumerate(week):
            if day != 0:
                text_fill = 'black'
                weight = 'normal'

                # 元の計算式に基づいた座標
                center_x = j * cell_width + 20
                center_y = (i + 2) * cell_height - 10

                if day == current_day:
                    # 今日を黒丸白抜きで強調
                    # 元の座標 y から少し上にずらすと数字が中央に見えます
                    circle_y = center_y - 8 
                    dwg.append(draw.Circle(center_x, circle_y, 14, fill='black'))
                    text_fill = 'white'
                    weight = 'bold'
                
                dwg.append(draw.Text(
                    str(day), 
                    font_size=font_size_val, 
                    x=center_x, 
                    y=center_y, 
                    text_anchor='middle',
                    font_weight=weight,
                    fill=text_fill
                ))

    svg_output = dwg.as_svg()
    if '\n' in svg_output:
        svg_output = svg_output.split('\n', 1)[1]

    output_svg_filename = 'screen-output-weather.svg'
    output_dict = {'MONTH_CAL': svg_output}
    update_svg(output_svg_filename, output_svg_filename, output_dict)

if __name__ == "__main__":
    main()
