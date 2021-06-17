from flask import request
from flask_restful import Resource, abort
from flask_jwt_extended import ( jwt_required, get_jwt)
from marshmallow import ValidationError
from zembil import db
from zembil.models import CategoryModel
from zembil.schemas import CategorySchema

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)

class Categories(Resource):
    def get(self):
        result = CategoryModel.query.all()
        return categories_schema.dump(result)
    
    @jwt_required()
    def post(self):
        role = get_jwt()['role']
        if role == 'user':
            abort(403, message="Requires admin privelege")
        data = request.get_json()
        try:
            args = category_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        category = CategoryModel(name=args['name'])
        db.session.add(category)
        db.session.commit()
        return category_schema.dump(category), 201

class Category(Resource):
    def get(self, id):
        result = CategoryModel.query.filter_by(id=id).first()
        if not result:
            abort(404, message="Category Not Found")
        return category_schema.dump(result)