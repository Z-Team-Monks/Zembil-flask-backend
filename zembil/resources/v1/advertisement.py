from flask import request
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import ( jwt_required, get_jwt, get_jwt_identity)
from marshmallow import ValidationError
from zembil import db
from zembil.models import AdvertisementModel
from zembil.schemas import AdvertisementSchema
from zembil.common.util import clean_null_terms

advertisement_schema = AdvertisementSchema()
advertisements_schema = AdvertisementSchema(many=True)

ad_arguments = reqparse.RequestParser()
ad_arguments.add_argument(
    'is_active', type=bool, help="is_active", required=True)

class Advertisements(Resource):
    def get(self):
        ads = AdvertisementModel.query.all()
        return advertisements_schema.dump(ads)

    # @jwt_required()
    def post(self):
        data = request.get_json()
        try:
            args = advertisement_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        ad = AdvertisementModel(**args)
        try:
            db.session.add(ad)
            db.session.commit()
            return advertisement_schema.dump(ad), 201
        except:
            abort(500, message="database error") 


class Advertisement(Resource):
    def get(self, id):
        ad = AdvertisementModel.query.get(id)
        if not ad:
            abort(404, message="Ad not found!")
        return advertisement_schema.dump(ad)

    @jwt_required()
    def patch(self, id):
        role = get_jwt()['role']
        if role == 'user':
            abort(403, message="Requires admin privelege")
        args = ad_arguments.parse_args()
        # args = clean_null_terms(args)
        if not args:
            abort(400, message="Empty json body")
        existing = AdvertisementModel.query.get(id)
        if existing:
            ad = AdvertisementModel.query.filter_by(id=id).update(args)
            db.session.commit()
            return advertisement_schema.dump(ad), 200
        abort(404, message="Ad doesn't exist!")
    
    @jwt_required()
    def delete(self, id):
        role = get_jwt()['role']
        if role == 'user':
            abort(403, message="Requires admin privelege")
        ad = AdvertisementModel.query.filter_by(id=id)
        if ad.first():
            ad.delete()
            db.session.commit()
            return 204      
        abort(404, message="Ad doesn't exist")
        