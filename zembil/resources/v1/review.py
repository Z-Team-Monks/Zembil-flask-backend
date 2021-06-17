from flask import request
from flask_restful import Resource, abort
from flask_jwt_extended import ( jwt_required, get_jwt_identity)
from marshmallow import ValidationError
from zembil import db
from zembil.models import (
    ReviewModel, ProductModel, UserModel, NotificationModel
    )
from zembil.schemas import ReviewSchema, ProductReviewSchema
from zembil.common.util import clean_null_terms

review_schema = ReviewSchema()
reviews_schema = ReviewSchema(many=True)
product_reviews_schema = ProductReviewSchema()

class Reviews(Resource):
    def get(self, product_id):
        product = ProductModel.query.filter_by(id=product_id).first()
        if product:
            return product_reviews_schema.dump(product)
        return abort(404, message="No one reviewed yet!")
    
    @jwt_required()
    def post(self, product_id):
        data = request.get_json()
        try:
            args = review_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        args = clean_null_terms(args)
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)
        product_exists = ProductModel.query.get(product_id)
        if not product_exists:
            abort(404, message="Product doesn't exist!")
        existing = ReviewModel.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not existing and args:
            review = ReviewModel(
                product_id=product_id,
                user_id=user_id,
                **args
            )
            notification = NotificationModel(
                    user_id=user_id,
                    notification_message=f"{user.username} reviewed {product_exists.name} from your shop {product_exists.shop.name}.",
                    notification_type="New Product"
                )
            db.session.add(review)
            db.session.add(notification)
            db.session.commit()
            return review_schema.dump(review), 201
        return abort(409, message="User already rated this product")

class Review(Resource):
    def get(self, product_id, id):
        review = ReviewModel.query.filter_by(id=id).first()
        if review:
            return review_schema.dump(review)
        return abort(404, message="Review doesn't exist!")

    @jwt_required()
    def delete(self, product_id, id):
        review = ReviewModel.query.get(id)
        if review:
            db.session.delete(review)
            db.session.commit()
            return {"message": "Successfull"}, 204
        abort(404, message="Review doesn't exist!")

    @jwt_required()
    def patch(self, product_id, id):
        data = request.get_json()
        try:
            args = ReviewSchema(partial=True).load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        existing = ReviewModel.query.get(id)
        args = clean_null_terms(args)
        user_id = get_jwt_identity()
        if existing and existing.user_id == user_id:
            review = ReviewModel.query.filter_by(id=id).update(args)
            db.session.commit()
            return review_schema.dump(review), 200
        abort(404, message="Review doesn't exist")


