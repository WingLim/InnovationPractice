from model import Route
from model import Stop
from model import Bus
from bus_spider import BusSpider


def get_routes() -> list[(int, str), ...]:
    all_routes = Route().get_all()
    routes = []
    for route in all_routes:
        a_route = (route.route_id, route.name)
        routes.append(a_route)
    return routes


def get_bus_position(route_id: int) -> list['Bus', ...]:
    return BusSpider().get_bus_position(route_id)


def get_stops_by(route_id: int) -> list['Stop', ...]:
    route = Route().find_by_id(route_id)
    stop_ids = route.stops.split(',')[1:]
    stops = []
    for stop_id in stop_ids:
        a_stop = Stop().find_by_id(stop_id)
        stops.append(a_stop)
    return stops


if __name__ == '__main__':
    print(get_routes())
    print(get_bus_position(1001000003))
    print(get_stops_by(1001000003))

