import flet as ft
import requests
import sqlite3
from datetime import datetime

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
DB_PATH = "weather.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT,
            area_name TEXT,
            time TEXT,
            weather_text TEXT,
            created_at TEXT,
            UNIQUE(area_code, time)
        )
        """
    )
    conn.commit()
    conn.close()


def insert_forecast(area_code, area_name, times, weathers):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for t, w in zip(times, weathers):
        cur.execute(
            """
            INSERT OR REPLACE INTO weather_forecast
            (area_code, area_name, time, weather_text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (area_code, area_name, t, w, now),
        )
    conn.commit()
    conn.close()


def load_forecast_from_db(area_code):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT area_name, time, weather_text
        FROM weather_forecast
        WHERE area_code = ?
        ORDER BY time
        """,
        (area_code,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def main(page: ft.Page):
    page.title = "気象庁API + SQLite サンプル"
    page.vertical_alignment = ft.MainAxisAlignment.START

    init_db()

    area_dd = ft.Dropdown(label="地域を選択", width=300)
    get_btn = ft.ElevatedButton("APIから取得してDB保存")
    show_btn = ft.ElevatedButton("DBから表示")
    result = ft.Text("ここに天気予報が表示されます", selectable=True)

    # 地域リスト取得
    def load_areas():
        try:
            r = requests.get(AREA_URL, timeout=10)
            data = r.json()
            offices = data["offices"]
            area_dd.options = [
                ft.dropdown.Option(code, offices[code]["name"])
                for code in offices.keys()
            ]
            page.update()
        except Exception as e:
            result.value = f"地域取得エラー: {e}"
            page.update()

    # API→DB保存
    def get_weather(e):
        code = area_dd.value
        if not code:
            result.value = "地域を選択してください。"
            page.update()
            return
        try:
            r = requests.get(FORECAST_URL.format(code=code), timeout=10)
            data = r.json()
            ts = data[0]["timeSeries"][0]
            area = ts["areas"][0]
            name = area["area"]["name"]
            times = ts["timeDefines"]
            weathers = area["weathers"]

            # DBに保存
            insert_forecast(code, name, times, weathers)

            result.value = "APIから取得し、DBに保存しました。『DBから表示』を押してください。"
        except Exception as ex:
            result.value = f"天気取得エラー: {ex}"
        page.update()

    # DB→表示
    def show_weather(e):
        code = area_dd.value
        if not code:
            result.value = "地域を選択してください。"
            page.update()
            return
        rows = load_forecast_from_db(code)
        if not rows:
            result.value = "DBにデータがありません。先に『APIから取得してDB保存』を押してください。"
        else:
            area_name = rows[0][0]
            text = f"地域: {area_name}\n\n"
            for _, t, w in rows:
                text += f"{t} : {w}\n"
            result.value = text
        page.update()

    get_btn.on_click = get_weather
    show_btn.on_click = show_weather

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        leading=ft.Text("メニュー"),
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.CLOUD, label="天気"),
        ],
    )

    right = ft.Column(
        [
            ft.Row([area_dd, get_btn, show_btn]),
            ft.Divider(),
            ft.Container(content=result, expand=True, padding=10),
        ],
        expand=True,
    )

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                right,
            ],
            expand=True,
        )
    )

    load_areas()


ft.app(target=main)