import flet as ft
import requests


AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"


def main(page: ft.Page):
    page.title = "気象庁APIサンプル"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # UI部品
    area_dd = ft.Dropdown(label="地域を選択", width=300)
    get_btn = ft.ElevatedButton("天気取得")
    result = ft.Text("ここに天気予報が表示されます", selectable=True)

    # 1. 起動時に地域リスト取得
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

    # 2. 選択地域の天気取得
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

            text = f"地域: {name}\n\n"
            for t, w in zip(times, weathers):
                text += f"{t} : {w}\n"
            result.value = text
        except Exception as ex:
            result.value = f"天気取得エラー: {ex}"
        page.update()

    get_btn.on_click = get_weather

    # 左ナビ
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        leading=ft.Text("メニュー"),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.CLOUD, label="天気"
            ),
        ],
    )

    # 右側コンテンツ
    right = ft.Column(
        [
            ft.Row([area_dd, get_btn]),
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