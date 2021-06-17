from flask import request
from flask_restful import Resource, abort
from sqlalchemy import func
from marshmallow import ValidationError
from zembil import db
from zembil.models import LocationModel, ShopModel
from zembil.schemas import LocationSchema, ShopSchema

location_schema = LocationSchema()
locations_schema = LocationSchema(many=True)
shops_schema = ShopSchema(many=True)

class Locations(Resource):
    def get(self):
        results = LocationModel.query.all()
        return locations_schema.dump(results)

    def post(self):
        data = request.get_json()
        try:
            args = location_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        existingLocation = LocationModel.query.filter_by(
            latitude=args['latitude'],
            longitude=args['longitude']
        )
        if existingLocation:
            abort(409, message="Shop with this location already exists")
        location = LocationModel(
            latitude=args['latitude'], 
            longitude=args['longitude'], 
            description=args['description']
        )
        db.session.add(location)
        db.session.commit()
        return location_schema.dump(location), 201

class Location(Resource):
    def get(self, id):
        result = LocationModel.query.filter_by(id=id).first()
        if not result:
            abort(404, message="Location Not Found")
        return location_schema.dump(result)


class LocationNearMe(Resource):
    def get(self):
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        radius = request.args.get('radius')
        if not radius:
            radius = 10
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
            locations =  LocationModel.query.filter(
                func.acos(func.sin(func.radians(latitude)) \
                * func.sin(func.radians(LocationModel.latitude)) \
                + func.cos(func.radians(latitude)) \
                * func.cos(func.radians(LocationModel.latitude)) \
                * func.cos(func.radians(LocationModel.longitude) \
                - (func.radians(longitude)))) * 6371 <= radius)
            locations_id = [location.id for location in locations.all()]
            result = db.session.query(ShopModel).filter(ShopModel.location_id.in_(locations_id)).all()
            return shops_schema.dump(result)
        abort(400, message="No shops found near your location")