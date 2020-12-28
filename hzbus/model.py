import typing
from db import RouteDb, StopDb


class Route:
    def __init__(self):
        self.route_id = None
        self.opposite_id = None
        self.amap_id = None
        self.name = ""
        self.raw_name = ""
        self.origin = ""
        self.terminal = ""
        self.has_gps = False
        self.stops = ""

    def create(self):
        data = self.__dict__
        RouteDb.create(**data)

    @classmethod
    def find_by_id(cls, route_id: int):
        return RouteDb.get_or_none(RouteDb.route_id == route_id)

    @classmethod
    def get_id_by_raw_name(cls, route_name: str, origin, terminal) -> int:
        query = RouteDb.get_or_none(RouteDb.name == route_name, RouteDb.origin == origin, RouteDb.terminal == terminal)
        if query:
            return query.route_id
        else:
            return 0

    @classmethod
    def add_a_stop(cls, route_id: int, stop_id: int):
        """添加一个站点到公交线路中
        """
        query = RouteDb.update(stops=RouteDb.stops + ',' + stop_id).where(RouteDb.route_id == route_id)
        query.execute()

    @classmethod
    def get_all(cls) -> typing.List['Route']:
        """获取所有公交线路
        """

        query = RouteDb.select()
        result = []
        for item in query:
            route = cls()
            route.__dict__.update(item.__data__)
            route.stops = route.stops.split(',')[1:]
            result.append(route)
        return result

    @classmethod
    def get_all_with_stop_name(cls):
        """获取所有公交线路和经过的站点的名称
        """

        # Todo
        # 时间复杂度O(n^2)了，需要优化

        routes = cls.get_all()
        for route in routes:
            stops = []
            for stop_id in route.stops:
                item = Stop.find_by_id(stop_id)
                stops.append(item.name)
            route.stops = stops
        return routes

class Stop:
    def __init__(self):
        self.stop_id = None
        self.amap_id = None
        self.name = ""
        self.lng = None # 经度
        self.lat = None # 纬度
        self.routes = ""

    def create(self):
        data = self.__dict__
        StopDb.create(**data)

    @classmethod
    def find_by_id(cls, stop_id: int) -> 'Stop':
        query = StopDb.get_or_none(StopDb.stop_id == stop_id)
        if query:
            stop = cls()
            stop.__dict__.update(query.__data__)
            return stop

    @classmethod
    def get_id_by_name(cls, stop_name: str) -> int:
        query = StopDb.get_or_none(StopDb.name == stop_name)
        if query:
            return query.stop_id
        return 0

    @classmethod
    def get_all(cls) -> typing.List['Stop']:
        query = StopDb.select()
        result = []
        for item in query:
            stop = cls()
            stop.__dict__.update(item.__data__)
            result.append(stop)
        return result


if __name__ == '__main__':
    #result = Route.get_all_with_stop_name()
    #print(result[0].__dict__)
    #print(len(result[0].stops))
    # def check_route_stops():
    #     """测试代码，检测一下数据库里爬的内容是否正确
    #     但目前来看缺少了不少路线的站点 id 数据
    #     """
    #     with open('stops_dict.json', 'r') as f:
    #         import json
    #         stops_dict = json.load(f)
    #     route_data = Route.get_all_with_stop_name()
    #     print('获取站点数据成功')
    #     for route in route_data:
    #         if route.name in stops_dict:
    #             raw = stops_dict[route.name]
    #             raw_len = [len(i) for i in raw]
    #             if len(route.stops) not in raw_len:
    #                 print(f'{route.name} 线路站点数量不匹配')
    #                 print(f'数据库中的数量为 {len(route.stops)}')
    #                 print(f'获取的数量为 {raw_len}')
    #                 for line in raw:
    #                     print(set(line) - set(route.stops))
    # check_route_stops()
    print(Route.get_id_by_name('1路'))