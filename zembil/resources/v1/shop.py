from flask import request
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import ( jwt_required, get_jwt_identity, get_jwt)
from marshmallow import ValidationError
from zembil import db
from zembil.models import UserModel, ShopModel, LocationModel, CategoryModel
from zembil.schemas import ShopSchema, LocationSchema, TotalShopFollowerSchema
from zembil.common.util import clean_null_terms

shop_schema = ShopSchema()
location_schema = LocationSchema()

shops_schema = ShopSchema(many=True)
shops_followers_schema = TotalShopFollowerSchema(many=True)

shop_status_arguments = reqparse.RequestParser()
shop_status_arguments.add_argument('isActive', type=bool, help="Status is required", required=True)

class Shops(Resource):
    def get(self):
        result = ShopModel.query.all()
        return shops_followers_schema.dump(result)

    @jwt_required()
    def post(self):
        data = request.get_json()
        try:
            location_args = location_schema.load(data['location'])
            shop_args = shop_schema.load(data['shop'])
        except ValidationError as errors:
            abort(400, message=errors.messages)
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)
        if user:
            existing_location = LocationModel.query.filter_by(
                latitude=location_args['latitude'],
                longitude=location_args['longitude']
                ).first()
            if existing_location:
                abort(409, message="Shop with this location already exists")
            try:
                location = LocationModel(
                    **location_args
                )
                db.session.add(location)
            except:
                abort(500, message="Database error")
            try:
                shop = ShopModel(
                    user_id=user_id,
                    **shop_args)
                shop.location = location
                db.session.add(shop)
            except:
                abort(500, message="Database error")
            
            db.session.commit()
            return shop_schema.dump(shop), 201
        abort(404, message="User Doesn't Exist")


class Shop(Resource):
    def get(self, id):
        result = ShopModel.query.filter_by(id=id).first()
        if result:
            return shop_schema.dump(result)
        abort(404, message="Shop Doesn't Exist")
    
    @jwt_required()
    def patch(self, id):
        data = request.get_json()
        try:
            args = ShopSchema(partial=True).load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        args = clean_null_terms(args)
        if not args:
            abort(400, message="Empty json body was given!")
        user_id = get_jwt_identity()
        existing = ShopModel.query.filter_by(id=id)
        if existing.first():
            if existing.first().user_id == user_id:
                shop = existing.update(args)
                db.session.commit()
                return shop_schema.dump(existing.first()), 200
            abort(403, message="Shop doesn't belong to this user!")
        abort(404, message="Shop doesn't exist!")

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        shop = ShopModel.query.get(id)
        if shop and shop.user_id == user_id:
            db.session.delete(shop)
            db.session.commit()
            return 204
        if shop:
            abort(403, message="User is not owner of this shop!")
        abort(404, message="Shop doesn't exist!")


class UserShops(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)
        return shops_schema.dump(user.shops)


class SearchShop(Resource):
    def get(self):
        name = request.args.get('name')
        category = request.args.get('category')
        shops = ShopModel.query
        if name:
            shops = shops.filter(ShopModel.name.ilike('%' + name + '%'))
        if category:
            shops = shops.filter(CategoryModel.name.ilike('%' + category + '%'))
        shops = shops.order_by(ShopModel.name).all()
        if shops:
            return shops_schema.dump(shops)
        abort(404, message="Product doesn't exist!")

class ApproveShop(Resource):
    @jwt_required()
    def patch(self, id):
        args = shop_status_arguments.parse_args()
        status = args['isActive']
        role = get_jwt()['role']
        if role == 'user':
            abort(403, message="Higher Privelege required")
        shop = ShopModel.query.filter_by(id=id)
        if not status:
              shop.delete()
        else:  
            shop.first().status = status
        db.session.commit()
        return shop_schema.dump(shop), 204
