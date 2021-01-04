import time
import hmac
import json
import base64
import requests
from urllib.parse import quote
from hashlib import sha256
from model import Bus


class BusSpider:
    def __init__(self):
        self.url = 'https://app.ibuscloud.com/v2/bus/'
        self.base_data = {
            'uuid': 'AC455F28-C328-41BC-B375-12118B80CFF4',
            'access_id': 'ptapp',
            'timestamp': '',
            'city': 330100,
            'token': '',
            'appSource': 'com.dtdream.publictransit',
            'platform': 'iOS',

            'routeId': 0,
            'deviceId': '3374261eaeff9e237e0caeab197c5d467aa5cf7d43a20932cb6508ea3c1ee473',
        }

    def gen_raw_str(self, base_data: dict) -> str:
        str_arr = list(base_data.keys())
        str_arr.sort()
        result = 'GET'
        result += '&'
        result += '%2F'
        result += '&'
        for key in str_arr:
            result += str(key)
            result += '%3D'
            result += str(base_data[key])
            result += '%26'
        return result[0:-3]

    def gen_signature(self, raw_str) -> str:
        key = '23c2f22fadf46f3b28b6adddd242959e&'.encode('utf-8')
        message = raw_str.encode('utf-8')
        sign = base64.b64encode(
            hmac.new(key, message, digestmod=sha256).digest())
        sign = str(sign, 'utf-8')
        return quote(sign).replace('/', '%2F')

    def gen_href(self, data: dict, signature: str):
        data['signature'] = signature
        href = self.url
        for key, val in data.items():
            href += str(key)
            href += '='
            href += str(val)
            href += '&'
        return href[0:-1]

    def parse_position(self, raw: str) -> list['Bus', ...]:
        data = json.loads(raw)
        buses = []
        for bus in data['items'][0]['routes'][0]['nextBuses']['buses']:
            a_bus = Bus()
            a_bus.id = bus['busId']
            a_bus.lng = bus['lng']
            a_bus.lat = bus['lat']
            a_bus.plate = bus.get('busPlate', '')
            buses.append(a_bus)
        return buses

    def crawl_bus_position(self, route_id: int) -> str:
        self.url += 'getBusPositionByRouteId?'
        self.base_data['routeId'] = route_id
        self.base_data['timestamp'] = int(time.time() * 1000)
        raw_str = self.gen_raw_str(self.base_data)
        signature = self.gen_signature(raw_str)
        href = self.gen_href(self.base_data, signature)
        r = requests.get(href)
        return r.text

    def get_bus_position(self, route_id: int) -> list['Bus', ...]:
        result = self.crawl_bus_position(route_id)
        return self.parse_position(result)


if __name__ == '__main__':
    spider = BusSpider()
    data = spider.get_bus_position(1001000003)
    print(data)
