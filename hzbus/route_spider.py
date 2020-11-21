import os
import json
import requests
import threading
import typing
import time
from lxml import etree
from urllib.parse import quote
from model import Route, Stop


class RouteSpider:
    def __init__(self):
        self.url = 'https://hangzhou.8684.cn'
        self.ibuscloud = 'https://app.ibuscloud.com/v1/bus/'
        self.city_id = 330100
        self.routes = []
        self.stops = []
        self.routes_queue = 'routes-remain.json'
        self.stops_queue = 'stops_remain.json'
        self.stops_dict_queue = 'stops_dict_remain.json'
        self.stops_dict = {}
        self.route_ids = []
        self.stop_ids = []

    def get_all_route_name(self):
        """获取所有公交线路名称，用于获取详细信息
        """
        for i in range(1, 7):
            url = self.url + '/line' + str(i)
            print(url)
            r = requests.get(url)
            tree = etree.HTML(r.text)
            routes = tree.xpath('//div[@class="list clearfix"]/a')
            for route in routes:
                name = route.xpath('./text()')[0]
                href = self.url + route.xpath('@href')[0]
                self.routes.append((name, href))
        with open('routes.json', 'w') as f:
            f.write(json.dumps(self.routes, ensure_ascii=False))

    def get_all_stop_name(self):
        """获取所有公交站点名称，用于获取详细信息
        """

        filename = self.stops_dict_queue
        if not os.path.exists(filename):
            queue = self.routes
        else:
            with open(filename, 'r') as f:
                queue = json.load(f)
        self._start_tasks(queue, self.get_stop_name)
        self._remove_queue_file(filename)

    def get_stop_name(self, queue: list):
        while len(queue):
            item = queue.pop(0)
            route_name = item[0]
            href = item[1]
            self.stops_dict[route_name] = [[], []]
            print("正在爬取 %s 公交经过的站点" % route_name)
            time.sleep(1)
            r = requests.get(href)
            tree = etree.HTML(r.text)
            lines = tree.xpath('//div[@class="bus-lzlist mb15"]')
            for i in range(len(lines)):
                stops = lines[i].xpath('./ol/li/a')
                for stop in stops:
                    name = stop.xpath('./text()')[0]
                    self.stops_dict[route_name][i].append(name)
                    self.stops.append(name)

            with open(self.stops_dict_queue, 'w') as f:
                f.write(json.dumps(queue, ensure_ascii=False))
            
            with open('stops.json', 'w') as f:
                f.write(json.dumps(self.stops, ensure_ascii=False))
        
            with open('stops_dict.json', 'w') as f:
                f.write(json.dumps(self.stops_dict, ensure_ascii=False))
    
    def load_data(self):
        if os.path.exists('routes.json'):
            with open('routes.json', 'r') as f:
                self.routes = json.load(f)
                print(len(self.routes))

        if os.path.exists('stops.json'):
            with open('stops.json', 'r') as f:
                data = json.load(f)
                self.stops = list(set(data))
                print(len(self.stops))

    def _start_tasks(self, queue: list, func, num: int = 5):
        tasks = []
        for i in range(5):
            task = threading.Thread(target=func, args=(queue,))
            tasks.append(task)
            task.start()
        
        for task in tasks:
            task.join()

    def _remove_queue_file(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                queue = json.load(f)
            if not len(queue):
                os.remove(filename)

    def get_all_route_details(self):
        filename = self.routes_queue
        if not os.path.exists(filename):
            queue = [i[0] for i in self.routes]
        else:
            with open(filename, 'r') as f:
                queue = json.load(f)
        self._start_tasks(queue, self.get_route_details)
        #self.get_route_details(queue)
        self._remove_queue_file(filename)
    
    def get_route_details(self, queue: list):
        while len(queue):
            name = queue.pop(0)
            print("正在爬取 %s 的详细信息" % name)
            with open(self.routes_queue, 'w') as f:
                json.dump(queue, f)
            time.sleep(1)
            result = self.find_route_by_name(name)
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
            # if item['name'] == name:
            # 这里去掉名称检测，因为爬取到的路的名称和通过 API 获取到的有一部分有出入
            # 这样能尽量获取所有线路信息
            for route in item['routes']:
                route_id = route['routeId']
                # 如果获取到的线路的 id 在 route_ids 里面，则跳过，剩下的全部插入到数据库中
                if route_id in self.route_ids:
                    continue
                else:
                    self.route_ids.append(route_id)
                a_route = Route()
                a_route.route_id = route_id
                if 'oppositeId' in route:
                    a_route.opposite_id = route['oppositeId']
                if 'amapId' in route:
                    a_route.amap_id = route['amapId']
                a_route.name = route['routeName']
                a_route.origin = route['origin']
                a_route.terminal = route['terminal']
                a_route.has_gps = route['hasGps']
                routes.append(a_route)

        return routes

    def get_all_stop_details(self):
        filename = self.stops_queue
        if not os.path.exists(filename):
            queue = self.stops
        else:
            with open(filename, 'r') as f:
                queue = json.load(f)
        self._start_tasks(queue, self.get_stop_details)
        self._remove_queue_file(filename)

    def get_stop_details(self, queue: list):
        while len(queue):
            # 保存下来的的公交站点名为 XXX站
            # 根据站名查找时需要去掉'站'
            name = queue.pop()
            print("正在爬取 %s 的详细信息" % name)
            with open(self.stops_queue, 'w') as f:
                json.dump(queue, f)
            time.sleep(1)
            result = self.find_stop_by_name(name)
            if len(result):
                for item in result:
                    item.create()

    def find_stop_by_name(self, name: str) -> typing.List[Stop]:
        path = 'findStopByName?city=%d&h5Platform=6&stopName=' % self.city_id
        href = self.ibuscloud + path + quote(name)
        r = requests.get(href)
        result = json.loads(r.text)
        if result['total'] != 0:
            return self._parse_stop(result, name)
        else:
            return []

    def _parse_stop(self, content: dict, name: str) -> typing.List[Stop]:
        stops = []
        for item in content['items']:
            if item['name'] == name:
                for stop in item['stops']:
                    stop_id = stop['stopId']
                    if stop_id in self.stop_ids:
                        continue
                    else:
                        self.stop_ids.append(stop_id)
                    a_stop = Stop()
                    a_stop.name = name
                    a_stop.stop_id = stop['stopId']
                    if 'amapId' in stop:
                        a_stop.amap_id = stop['amapId']
                    a_stop.lng = stop['lng']
                    a_stop.lat = stop['lat']
                    a_stop.routes = ','.join(self._parse_stop_routes(stop_id, stop['routeInfos']))
                    stops.append(a_stop)

        return stops

    def _parse_stop_routes(self, stop_id: int,infos: list):
        routes_id = []
        for info in infos:
            routes_id.append(str(info['routeId']))
            self._add_stop_route(stop_id, info['routeId'])

        return routes_id
    
    def _add_stop_route(self, stop_id: int, route_id: int):
        # 获取到通过当前站点的公交路线 ID 后，在数据库中查询该公交线路
        # 并将站点 ID 更新到 stops 中
        route = Route.find_by_id(route_id)
        if route:
            print('正在更新 %s 的站点信息' % route.name)
            Route.add_a_stop(route_id, stop_id)
    

if __name__ == '__main__':
    spider = RouteSpider()
    #spider.get_all_route_name()
    #spider.load_data()
    #spider.get_all_stop_name()
    spider.load_data()
    spider.get_all_route_details()
    spider.get_all_stop_details()
    
