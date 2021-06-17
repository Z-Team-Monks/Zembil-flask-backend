import os
from flask import current_app, request, url_for
from flask_restful import Resource, abort
from flask_jwt_extended import ( jwt_required, get_jwt_identity)
from werkzeug.utils import secure_filename
from zembil import db
from zembil.models import ShopModel, ProductModel
from zembil.schemas import ShopSchema, ProductSchema

class UploadShopImage(Resource):
    @jwt_required()
    def post(self, shop_id):
        existing = ShopModel.query.get(shop_id)
        user_id = get_jwt_identity()
        if existing.user_id == user_id:
            image = request.files['file']
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                path = current_app.config['UPLOAD_FOLDER'] + "/shops"
                image.save(os.path.join(path, filename))
                path = path.replace("./zembil", "")
                shop = ShopModel.query.filter_by(id=shop_id).update({"image": path + "/" + filename})
                db.session.commit()
                return ShopSchema().dump(ShopModel.query.get(shop_id)), 201
            abort(400, message="File was not properly sent!")
        abort(403, message="User is not owner of this shop!")

class UploadProductImage(Resource):
    @jwt_required()
    def post(self, product_id):
        existing = ProductModel.query.get(product_id)
        user_id = get_jwt_identity()
        if existing.shop.user_id == user_id:
            image = request.files['file']
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                path = current_app.config['UPLOAD_FOLDER'] + "/products"
                image.save(os.path.join(path, filename))
                path = path.replace("./zembil", "")
                product = ProductModel.query.filter_by(id=product_id).update({"image": path + "/" + filename})
                db.session.commit()
                return ProductSchema().dump(ProductModel.query.get(product_id)), 201
            abort(400, message="File was not properly uploaded")
        abort(403, message="User is not owner of this shop!")
    