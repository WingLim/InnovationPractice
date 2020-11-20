from db import RouteDb, StopDb


class Route:
    def __init__(self):
        self.route_id = None
        self.opposite_id = None
        self.amap_id = None
        self.name = ""
        self.origin = ""
        self.terminal = ""
        self.has_gps = False
        self.stops = []

    def create(self):
        data = self.__dict__
        RouteDb.create(**data)

class Stop:
    def __init__(self):
        self.stop_id = None
        self.amap_id = None
        self.name = ""
        self.lng = None # 经度
        self.lat = None # 纬度
        self.routes = []

    def create(self):
        data = self.__dict__
        StopDb.create(**data)