from peewee import SqliteDatabase, Model, CharField, TextField, IntegerField, DoubleField, BooleanField

db = SqliteDatabase('hzbus.db')

class BasicModel(Model):
    class Meta:
        database = db

class RouteDb(BasicModel):

    route_id = IntegerField(primary_key=True, unique=True)
    opposite_id = IntegerField(null=True)
    amap_id = IntegerField(null=True)
    name = CharField()
    origin = CharField()
    terminal = CharField()
    has_gps = BooleanField()
    stops = TextField(null=True)

class StopDb(BasicModel):

    stop_id = IntegerField(primary_key=True, unique=True)
    amap_id = IntegerField()
    name = CharField()
    lng = DoubleField()
    lat = DoubleField()
    routes = TextField()


if __name__ == '__main__':
    db.connect()
    db.create_tables([RouteDb, StopDb])