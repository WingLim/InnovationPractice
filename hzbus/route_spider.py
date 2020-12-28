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

        self.routes_queue = 'routes_queue_cache.json'
        self.stops_queue = 'stops_queue_cache.json'
        self.stops_dict_queue = 'stops_dict_queue_cache.json'

        self.stops_dict = {}
        self.route_ids = []
        self.stop_ids = []

    def get_all_route_name(self):
        """获取所有公交线路名称，用于获取详细信息
        """
        # 按照线路类别来爬取，总共有11种类别
        # 分别为：常规线、假日线、萧山线、夜间线、余杭线
        # 高峰线、地铁线、定制线、富阳线、临安线、专线
        for i in range(1, 12):
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
            self.stops_dict[route_name] = []
            print("正在爬取 %s 公交经过的站点" % route_name)
            time.sleep(1)
            r = requests.get(href)
            tree = etree.HTML(r.text)
            lines = tree.xpath('//div[@class="bus-lzlist mb15"]')
            # 一条线路可能包含正向和反向，根据线路数量添加子列表
            for i in range(len(lines)):
                self.stops_dict[route_name].append([])
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

        if os.path.exists('stops_dict.json'):
            with open('stops_dict.json', 'r') as f:
                self.stops_dict = json.load(f)
                print(len(self.stops_dict))

    def _start_tasks(self, queue: list, func, num: int = 5):
        tasks = []
        lock = threading.RLock()
        for i in range(num):
            task = threading.Thread(target=func, args=(queue, lock))
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
        # 检查队列缓存文件，有则加载，没有则从 self.routes 获取线路名
        if not os.path.exists(filename):
            queue = [i[0] for i in self.routes]
        else:
            with open(filename, 'r') as f:
                queue = json.load(f)
        # 启动多线程爬取
        self._start_tasks(queue, self.get_route_details)
        #self.get_route_details(queue)
        # 爬取完毕，删除队列缓存文件
        self._remove_queue_file(filename)
    
    def get_route_details(self, queue: list, lock: threading.RLock):
        while len(queue):
            # 从队列头部取出
            lock.acquire()
            name = queue.pop(0)
            lock.release()
            print("正在爬取 %s 的详细信息" % name)
            time.sleep(1)
            # 根据名字查找线路信息，并插入到数据库
            result = self.find_route_by_name(name)
            if len(result):
                for item in result:
                    item.create()
            # 爬取后再将剩余队列保存到缓存文件
            lock.acquire()
            with open(self.routes_queue, 'w') as f:
                json.dump(queue, f, ensure_ascii=False)
            lock.release()

    def find_route_by_name(self, name: str) -> typing.List[Route]:
        path = 'findRouteByName?city=%d&h5Platform=6&routeName=' % self.city_id
        href = self.ibuscloud + path + quote(name)
        r = requests.get(href)
        result = json.loads(r.text)

        # 结果不为 0，进行解析，为 0 返回空列表
        if result['total'] != 0:
            return self._parse_route(result, name)
        else:
            return []

    def _parse_route(self, content: dict, name: str) -> typing.List[Route]:
        routes = []
        # 用于记录在请求中找到的对应的线路信息的次数
        flag = 0
        for item in content['items']:
            # 一条公交线路最多有正向和反向，当正反向同时找到时，停止遍历
            if flag == 2:
                break
            for route in item['routes']:
                origin = route['origin']
                terminal = route['terminal']
                for tmp in self.stops_dict[name]:
                    if origin == tmp[0] and terminal == tmp[-1]:
                        flag += 1
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
                        a_route.raw_name = name
                        a_route.origin = route['origin']
                        a_route.terminal = route['terminal']
                        a_route.has_gps = route['hasGps']
                        routes.append(a_route)

        return routes

    def get_all_stop_details(self):
        filename = self.stops_dict_queue
        if not os.path.exists(filename):
            queue = self.stops_dict
        else:
            with open(filename, 'r') as f:
                queue = json.load(f)
        self._start_tasks(queue, self.get_stop_details)
        self._remove_queue_file(filename)

    def get_stop_details(self, queue: dict, lock: threading.RLock):
        while len(queue):
            # 保存下来的的公交站点名为 XXX站
            # 根据站名查找时需要去掉'站'
            # routes 为 ('route_name', [[route_stops], [route_stops]])
            lock.acquire()
            routes = queue.popitem()
            lock.release()
            time.sleep(1)

            for route in routes[1]:
                route_id = Route.get_id_by_raw_name(routes[0], route[0], route[-1])
                for stop_name in route:
                    stop_id = Stop.get_id_by_name(stop_name)
                    if not stop_id:
                        print("正在爬取 %s 的详细信息" % stop_name)
                        result = self.find_stop_by_name(stop_name)
                        if len(result):
                            for item in result:
                                item.create()
                    else:
                        self._add_stop_route(stop_id, route_id)
            # 爬取后再将剩余队列保存到缓存文件
            lock.acquire()
            with open(self.stops_queue, 'w') as f:
                json.dump(queue, f, ensure_ascii=False)
            lock.release()


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
