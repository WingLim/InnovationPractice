import requests
from flask import Flask
from flask import request
from flask import Response
from flask import render_template
from flask import send_from_directory

from api import get_routes
from amap import build_url

app = Flask(__name__,
            template_folder='templates')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/staticmap/<int:route_id>')
def static_map(route_id: int):
    with requests.get(build_url(route_id), allow_redirects=True) as r:
        return Response(r.content, content_type='image/png')


@app.route('/')
def index():
    route_id = request.args.get('route_id')

    raw_routes = get_routes()
    routes = {route_name: route_id for route_id,
              route_name in raw_routes}.items()
    route_ids = [i for _, i in routes]

    if not route_id:
        route_id = route_ids[0]

    try:
        route_id = int(route_id)
        assert route_id in route_ids
    except:
        return Response("invalid route ID", status=400)

    route_name = dict(raw_routes)[route_id]

    return render_template('index.html',
                           routes=routes,
                           _route_id=route_id,
                           _route_name=route_name)


if __name__ == '__main__':
    app.run(debug=True)
