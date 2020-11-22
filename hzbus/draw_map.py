from flask import Flask
from model import Stop
import folium
import math

app = Flask(__name__)

def convert(lng, lat):
    x_PI = 3.14159265358979324 * 3000.0 / 180.0
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_PI)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_PI)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return [bd_lng, bd_lat]

m = folium.Map(
    location=[30.314192,120.343222],
    tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}',
    zoom_start=12,
    attr='高德地图'
)

stop_data = Stop.get_all()

def parse_zhch(chinese_str: str):
    """将中文转码，以便能正常显示
    """
    return str(str(chinese_str).encode('ascii' , 'xmlcharrefreplace'))[2:-1]

for stop in stop_data:
    folium.CircleMarker(
        location=[stop.lat, stop.lng],
        radius=2,
        popup=parse_zhch(stop.name)
    ).add_to(m)

@app.route('/')
def index():
    return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True)