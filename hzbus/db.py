from peewee import *

db = SqliteDatabase('hzbus.db')

class BasicModel(Model):
    class Meta:
        database = db

class RouteDb(BasicModel):

    id = PrimaryKeyField()
    route_id = IntegerField()
    opposite_id = IntegerField(null=True)
    amap_id = IntegerField(null=True)
    name = CharField()
    origin = CharField()
    terminal = CharField()
    has_gps = BooleanField()
    stops = TextField(null=True)

class StopDb(BasicModel):

    id = PrimaryKeyField()
    stop_id = IntegerField()
    amap_id = IntegerField(null=True)
    name = CharField()
    lng = DoubleField()
    lat = DoubleField()
    routes = TextField()


if __name__ == '__main__':
    db.connect()
    db.create_tables([RouteDb, StopDb])