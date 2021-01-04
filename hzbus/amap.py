import os
from random import choices
from urllib.parse import urljoin

from requests.models import PreparedRequest

from api import (get_bus_position,
                 get_routes,
                 get_stops_by)
from model import Bus
from model import Stop

token = os.getenv('TOKEN')
assert token is not None


def filter_stops(stops: list[Stop]) -> list[Stop]:
    m = {}
    for stop in stops:
        k = stop.name or stop.amap_id
        if k:
            m[k] = stop
    return list(m.values())


def build_markers(stops: list[Stop],
                  buses: list[Bus]
                  ) -> str:
    stop_markers = 'mid,0x4C9900,S:{!s}'.format(
        ';'.join(
            '{lng},{lat}'.format(**vars(stop)) for stop in stops if stop.lat and stop.lng
        )
    )

    bus_markers = 'large,0x6A5ACD,B:{!s}'.format(
        ';'.join(
            '{lng},{lat}'.format(**vars(bus)) for bus in buses if bus.lat and bus.lng
        )
    )

    return '|'.join([stop_markers, bus_markers])


def build_labels(stops: list[Stop]) -> str:
    _stops = choices(stops, k=10) if len(stops) > 10 else stops

    return '|'.join(
        '{name},,,16,,0x4C9900:{lng},{lat}'.format(**vars(stop))
        for stop in _stops if stop.lat and stop.lng
    )


def build_url(route_id: int):
    stops = filter_stops(
        get_stops_by(route_id))
    buses = get_bus_position(route_id)
    params = {
        'key': token,
        # 'zoom': 14,
        'size': '1024*512',
        'scale': 2,
        # 'traffic': 0,
        'markers': build_markers(stops, buses),
        'labels': build_labels(stops)
    }

    req = PreparedRequest()
    req.prepare_url(url='https://restapi.amap.com/v3/staticmap',
                        params=params)
    return req.url


if __name__ == '__main__':
    print(build_url(1001000010))
