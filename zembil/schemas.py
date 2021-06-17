import re
from marshmallow import fields, validate, validates, ValidationError
from zembil import ma
from zembil.models import *


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "username", "password", "email", "date", "role", "phone")
        model = UserModel
        ordered = True
    id = fields.Integer(dump_only=True, data_key="userId")
    name = fields.String(required=False)
    username = fields.String(required=True)
    password = fields.String(
        required=True, load_only=True, data_key="password")
    email = fields.Email(required=True)
    role = fields.String()
    phone = fields.String(required=False)
    date = fields.DateTime(dump_only=True, data_key="dateAccountCreated")

    @validates("phone")
    def validate_mobile(self, value):
        rule = re.compile(r'^\+(?:[0-9]●?){6,14}[0-9]$')

        if not rule.search(value):
            msg = u"Invalid mobile number."
            raise ValidationError(msg)

    @validates("username")
    def validate_username(self, username):
        if bool(UserModel.query.filter_by(username=username).first()):
            raise ValidationError(
                'username already exists, please use a different username.'
            )

    @validates("email")
    def validate_email(self, email):
        if bool(UserModel.query.filter_by(email=email).first()):
            raise ValidationError(
                'email already exists, please use a different email.'
            )


class LocationSchema(ma.Schema):
    class Meta:
        fields = ("id", "longitude", "latitude", "description")
        model = LocationModel
        ordered = True
    longitude = fields.Float(
        required=True, validate=lambda n: n > -180 and n < 180)
    latitude = fields.Float(
        required=True, validate=lambda n: n > -90 and n < 90)
    description = fields.String(
        required=True, validate=validate.Length(5), data_key="locationName")


class CategorySchema(ma.Schema):
    class Meta:
        fields = ("id", "name")
        model = CategoryModel
        ordered = True
    name = fields.String(required=True, data_key="categoryName")

class ShopSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "user_id", "location", "location_id", "category_id", "building_name", "phone_number1",
                  "phone_number2", "category", "image", "description", "status", "followers")
        model = ShopModel
        ordered = True
    name = fields.String(required=False, data_key="shopName")
    user_id = fields.Integer(data_key="userId")
    category_id = fields.Integer(required=True, data_key="categoryId")
    location_id = fields.Integer(data_key="shopLocationId")
    image = fields.String(required=False, data_key="imageUrl")
    category = fields.Pluck(CategorySchema, "name", dump_only=True)
    building_name = fields.String(required=False, data_key="buildingName")
    phone_number1 = fields.String(required=False, data_key="phoneNumber")
    phone_number2 = fields.String(required=False, data_key="phoneNumber2")
    description = fields.String(required=True)
    status = fields.Boolean(dump_only=True, data_key="isActive")

    location = ma.Nested(LocationSchema)
    followers = ma.Nested(UserSchema, only=['id'], many=True)

    @validates("phone_number1")
    @validates("phone_number2")
    def validate_mobile(self, value):
        rule = re.compile(r'^\+(?:[0-9]●?){6,14}[0-9]$')

        if not rule.search(value):
            msg = u"Invalid mobile number."
            raise ValidationError(msg)

class RatingSchema(ma.Schema):
    class Meta:
        fields = ("ratingcount", "averageRating")
        ordered = True
    averageRating = fields.Float(dump_only=True)
    ratingcount = fields.Integer(dump_only=True)


class ProductSchema(ma.Schema):
    class Meta:
        fields = ("id", "shop_id", "brand", "name", "date",
                  "description", "category", "category_id", "price", "condition", "image",
                  "delivery_available", "discount", "product_count", "rating")
        model = ProductModel
        ordered = True
    id = fields.Integer(dump_only=True, data_key="productId")
    name = fields.String(required=True, data_key="productName")
    date = fields.DateTime(dump_only=True, data_key="dateInserted")
    brand = fields.String(required=False, data_key="brand")
    shop_id = fields.Integer(required=True, data_key="shopId")
    category_id = fields.Integer(required=True, data_key="categoryId")
    category = fields.Pluck(CategorySchema, 'name', dump_only=True)
    description = fields.String(required=True, validate=validate.Length(5))
    price = fields.Float(required=True, validate=lambda n: n > 0)
    condition = fields.String(required=True)
    image = fields.String(required=False, data_key="imageUrl")
    delivery_available = fields.Boolean(
        required=False, data_key="deliveryAvailable")
    discount = fields.Float(required=False, validate=lambda n: n >= 0)
    product_count = fields.Integer(
        required=False, validate=lambda n: n >= 0, data_key="productCount")
    rating = fields.Float(dump_only=True)

    @validates("image")
    def validate_url(self, value):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not re.match(regex, value):
            msg = u"Invalid image url."
            raise ValidationError(msg)


class ShopProductSchema(ma.Schema):
    class Meta:
        fields = ("id", "products")
        model = ShopModel
        ordered = True
    id = fields.Integer(data_key="shopId")
    products = ma.List(ma.Nested(ProductSchema))


class AdvertisementSchema(ma.Schema):
    class Meta:
        fields = ("id", "shop_id", "discount", "is_active",  "start_date", "end_date", "description", "shop")
    id = fields.Integer(dump_only=True)
    shop_id = fields.Integer(required=True, data_key="shopId")
    start_date = fields.Date(required=True, data_key="startDate")
    end_date = fields.Date(required=True, data_key="endDate")
    description = fields.String()
    discount = fields.Float(required=True)
    is_active = fields.Boolean(dump_only=True)

    shop = ma.Nested(ShopSchema)


    # @validates("start_date")
    # def validate_date(self, value):
    #     present = datetime.now()
    #     if present > value:
    #         raise ValidationError("Date is in the past")

    # @validates("end_date")
    # def validate_end_date(self, value):
    #     if self.start_date > value:
    #         raise ValidationError("Start date is behind end date")


class ReviewSchema(ma.Schema):
    class Meta:
        fields = ("id", "user", "user_id", "product_id",
                  "rating", "review_text", "date")
        model = ReviewModel
        ordered = True
    rating = fields.Integer(required=False, validate=lambda n: n > 0 and n < 6)
    review_text = fields.String(required=False, data_key="comment")
    user = ma.Nested(UserSchema)
    user_id = fields.Integer(data_key="userId")
    product_id = fields.Integer(dump_only=True, data_key="productId")
    date = fields.DateTime(dump_only=True, data_key="reviewDate")


class ProductReviewSchema(ma.Schema):
    class Meta:
        fields = ("id", "reviews")
        model = ProductModel
        ordered = True
    id = fields.Integer(data_key="productId")
    reviews = ma.Nested(ReviewSchema(many=True), data_key="productReviews")


class CategoryShopsSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "shops")
        model = CategoryModel
        ordered = True
    shops = ma.Nested(ShopSchema(many=True))


class WishListSchema(ma.Schema):
    class Meta:
        fields = ("id", "product_id", "user_id", "date", "product")
        model = WishListModel
        ordered = True
    id = fields.Integer(dump_only=True, data_key="wishListItemId")
    user_id = fields.Integer(dump_only=True, data_key="userId")
    product_id = fields.Integer(required=True, data_key="productId")
    date = fields.DateTime(dump_only=True, data_key="dateAdded")
    product = ma.Nested(ProductSchema)


class UserWishListSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "email", "role", "phone", "wishlists")
        model = UserModel
        ordered = True
    wishlists = ma.List(ma.Nested(WishListSchema))


class ShopFollowerSchema(ma.Schema):
    class Meta:
        fields = ("user_id", "shop_id")
        model = ShopFollowerModel
        ordered = True
    user_id = fields.Integer(data_key="userId")
    shop_id = fields.Integer(data_key="shopId")


class TotalShopFollowerSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "user_id", "location", "location_id", "category_id", "building_name", "phone_number1",
                  "phone_number2", "category", "image", "description", "status", "followers")
        model = ShopModel
        ordered = True
    id = fields.Integer(data_key="shopId")
    user = ma.Nested(UserSchema)
    category = fields.Pluck(CategorySchema, "name", dump_only=True)
    location = ma.Nested(LocationSchema)
    followers = ma.Nested(ShopFollowerSchema, only=['user_id'], many=True)



class NotificationSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "notification_message",
                  "notification_type" "seen")
    id = fields.Integer(dump_only=True, data_key="notificationId")
    user_id = fields.String(dump_only=True, data_key="userId")
    notification_message = fields.String(
        dump_only=True, data_key="notificationMessage")
    notification_type = fields.String(
        dump_only=True, data_key="notificationType")
    seen = fields.Boolean(dump_only=True, data_key="seen")
