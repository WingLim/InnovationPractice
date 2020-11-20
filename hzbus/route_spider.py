import os
import json
import requests
import threading
import typing
from lxml import etree
from urllib.parse import quote
from model import Route, Stop


class RouteSpider:
    def __init__(self):
        self.url = 'https://bus.mapbar.com/hangzhou/xianlu/'
        self.ibuscloud = 'https://app.ibuscloud.com/v1/bus/'
        self.city_id = 330100
        self.routes = []
        self.stops = []

    def get_all_route_name(self):
        """获取所有公交线路名称，用于获取详细信息
        """

        r = requests.get(self.url)
        tree = etree.HTML(r.text)
        routes = tree.xpath('//dl[contains(@class, "ChinaTxt")]/dd/a')
        for route in routes:
            name = route.xpath('./text()')[0]
            href = route.xpath('@href')[0]
            self.routes.append((name, href))
        with open('routes.json', 'w') as f:
            f.write(json.dumps(self.routes))
        

    def get_all_stop_name(self):
        """获取所有公交站点名称，用于获取详细信息
        """

        for item in self.routes:
            print("正在爬取 %s 公交经过的站点" % item[0])
            r = requests.get(item[1])
            tree = etree.HTML(r.text)
            stops = tree.xpath('//ul[@id="scrollTr"]/li/a')
            for stop in stops:
                name = stop.xpath('./em/text()')[0]
                self.stops.append(name)
                
        print('before: ', len(self.stops))
        self.stops = list(set(self.stops))
        print('after: ', len(self.stops))
        with open('stops.json', 'w') as f:
            f.write(json.dumps(self.stops))
    
    def load_data(self):
        with open('routes.json', 'r') as f:
            self.routes = json.load(f)
            print(len(self.routes))

        with open('stops.json', 'r') as f:
            self.stops = json.load(f)
            print(len(self.stops))

    def get_all_route_details(self):
        for route in self.routes:
            result = self.find_route_by_name(route)
            if len(result):
                for item in result:
                    item.create()

    def find_route_by_name(self, name: str) -> typing.List[Route]:
        path = 'findRouteByName?city=%d&h5Platform=6&routeName=' % self.city_id
        href = self.ibuscloud + path + quote(name)
        r = requests.get(href)
        result = json.loads(r.text)

        if result['total'] != 0:
            return self._parse_route(result, name)
        else:
            return []

    def _parse_route(self, content: dict, name: str) -> typing.List[Route]:
        routes = []

        for item in content['items']:
            if item['name'] == name:
                for route in item['routes']:
                    a_route = Route()
                    a_route.route_id = route['routeId']
                    a_route.opposite_id = route['oppositeId']
                    a_route.name = route['routeName']
                    a_route.origin = route['origin']
                    a_route.terminal = route['terminal']
                    a_route.has_gps = route['hasGps']
                    routes.append(a_route)

        return routes


    def find_stop_by_name(self, name: str) -> typing.List[Stop]:
        path = 'findStopByName?city=%d&h5Platform=6&stopName=' % self.city_id
        href = self.ibuscloud + path + quote(name)
        r = requests.get(href)
        result = json.loads(r.text)
        return self._parse_stop(result, name)

    def _parse_stop(self, content: dict, name: str) -> typing.List[Stop]:
        stops = []

        for item in content['items']:
            if item['name'] == name:
                for stop in item["stops"]:
                    a_stop = Stop()
                    a_stop.name = name
                    a_stop.stop_id = stop["stopId"]
                    a_stop.lng = stop["lng"]
                    a_stop.lat = stop["lat"]
                    a_stop.routes.extend(self._parse_stop_routes(i["routeInfos"]))
                    stops.append(a_stop)

        return stops

    def _parse_stop_routes(self, infos: list):
        routes_id = []
        for info in infos:
            routes_id.append(info["routeId"])

        return routes_id
    
    def _add_stop_route(self, stop_id: int, route_id: int):
        # Todo
        # 获取到通过当前站点的公交路线 ID 后，在数据库中查询该公交线路
        # 并将站点 ID 更新到 stops 中
        pass
    

if __name__ == '__main__':
    spider = RouteSpider()
    spider.get_all_route_name()
    spider.get_all_stop_name()
