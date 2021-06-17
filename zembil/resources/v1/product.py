from flask import request, current_app, jsonify
from flask_jwt_extended.internal_utils import user_lookup
from flask_restful import Resource, abort
from flask_jwt_extended import ( jwt_required, get_jwt_identity)
from marshmallow import ValidationError
from sqlalchemy import func
from zembil import db
from zembil.models import (
    ProductModel, ShopModel, CategoryModel, ReviewModel, NotificationModel, UserModel
    )
from zembil.schemas import ProductSchema, ShopProductSchema, RatingSchema
from zembil.common.util import clean_null_terms
from zembil.common.helper import PaginationHelper

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

shop_products_schema = ShopProductSchema()

class Products(Resource):
    def get(self):
        limit = request.args.get('limit')
        results_per_page = current_app.config['PAGINATION_PAGE_SIZE']
        if limit:
            results_per_page = int(limit)
        pagination_helper = PaginationHelper(
            request,
            query=ProductModel.query,
            resource_for_url='api_v1.products',
            key_name='results',
            schema=products_schema,
            results_per_page=results_per_page
        )
        result = pagination_helper.paginate_query()
        return result
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        try:
            args = product_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        args = clean_null_terms(args)
        user_id = get_jwt_identity()
        shop_exists = ShopModel.query.filter_by(user_id=user_id).first()
        # if not shop_exists.status:
        #     abort(403, message="Shop status pending!")
        if shop_exists and shop_exists.user_id == user_id:
            product = ProductModel(**args)
            db.session.add(product)
            followers = shop_exists.followers
            for follower in followers:
                notification = NotificationModel(
                    user_id=follower.id,
                    notification_message=f"{shop_exists.name} added new product {product.name}",
                    notification_type="New Product"
                )
                db.session.add(notification)
            db.session.commit()
            return product_schema.dump(product), 201
        if shop_exists:
            abort(403, message="Shop doesn't belong to this user")
        abort(404, message="Shop doesn't exist")

class Product(Resource):
    def get(self, id):
        product = ProductModel.query.get(id)
        if product:
            average_rating = ReviewModel.query.with_entities(
                                    func.avg(ReviewModel.rating).label("sum")
                        ).filter_by(product_id=id).first()[0]
            ratingcount = ReviewModel.query.filter_by(product_id=id).count()
            data = product_schema.dump(product)
            if not average_rating:
                average_rating = 0.0
            rating = RatingSchema().dump({
                'averageRating': average_rating,
                'ratingcount': ratingcount
            })
            return jsonify({"product": data, "rating": rating})
        abort(404, message="Product doesn't exist!") 

    @jwt_required()
    def patch(self, id):
        data = request.get_json()
        try:
            args = ProductSchema(partial=True).load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        args = clean_null_terms(args)
        if not args:
            abort(400, message="Empty json body was given!")
        user_id = get_jwt_identity()
        existing = ProductModel.query.filter_by(id=id)
        if existing.first():
            if existing.first().shop.user_id == user_id:
                product = existing.update(args)
                db.session.commit()
                return product_schema.dump(existing.first()), 200
            abort(403, message="Product doesn't belong to this user!")
        abort(404, message="Product doesn't exist!")

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        product = ProductModel.query.filter_by(id=id)
        if product.first() and product.first().shop.user_id == user_id:
            product.delete()
            db.session.commit()
            return 204
        if product.first():
            abort(403, message="Product doesn't belong to this user!")
        abort(404, message="Ad doesn't exist")

class ShopProducts(Resource):
    def get(self, shop_id):
        shop = ShopModel.query.get(shop_id)
        if shop:
            return shop_products_schema.dump(shop)
        abort(404, message="Shop doesn't exist!")


class UserProducts(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)
        shop_ids = [shop.id for shop in user.shops]
        result = db.session.query(ProductModel).filter(ProductModel.shop_id.in_(shop_ids)).all()
        return products_schema.dump(result)

class SearchProduct(Resource):
    def get(self):
        name = request.args.get('name')
        category = request.args.get('category')
        products = ProductModel.query
        if name:
            products = products.filter(ProductModel.name.ilike('%' + name + '%'))
        if category:
            products = products.filter(CategoryModel.name.ilike('%' + category + '%'))
        products = products.order_by(ProductModel.name).all()
        if products:
            return products_schema.dump(products)
        abort(404, message="Product doesn't exist!")

class FilterProduct(Resource):
    def get(self):
        min_price = request.args.get('minPrice')
        max_price = request.args.get('maxPrice')
        products = ProductModel.query
        if min_price:
            products = products.filter(ProductModel.price >= float(min_price))
        if max_price:
            products = products.filter(ProductModel.price <= float(max_price))
        if products:
            return products_schema.dump(products)
        abort(404, message="Product doesn't exist!")


class TrendingProduct(Resource):
    def get(self):
        s = request.args.get('s')
        products = ProductModel.query
        if s:
            if s == 'latest':
                products = products.order_by(ProductModel.date.desc())
            if s == 'popular':
                sub_query = db.session.query(
                    ReviewModel.product_id, 
                    func.avg(ReviewModel.rating).label('rating')
                    ).group_by(ReviewModel.product_id).subquery()
                products = db.session.query(
                        ProductModel).join(
                    sub_query, 
                    ProductModel.id == sub_query.c.product_id
                    ).order_by(sub_query.c.rating.desc())
            results_per_page = current_app.config['PAGINATION_PAGE_SIZE']
            pagination_helper = PaginationHelper(
                request,
                query=products,
                resource_for_url='api_v1.trendingproduct',
                key_name='results',
                schema=products_schema,
                results_per_page=results_per_page
            )
            result = pagination_helper.paginate_query()
            return result
        abort(404, message="Product doesn't exist")

