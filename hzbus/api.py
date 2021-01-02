from model import Stop
from model import Bus
from bus_spider import BusSpider


def get_routes() -> list[(int, str), ...]:
    pass


def get_bus_position(route_id: int) -> list['Bus', ...]:
    return BusSpider().get_bus_position(route_id)


def get_stops_by(route_id: int) -> list['Stop', ...]:
    pass

