from datetime import timedelta
from markupsafe import escape
from flask import current_app, request, jsonify, make_response
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import (create_access_token, get_jwt,
                                jwt_required, get_jwt_identity)
from marshmallow import ValidationError
from zembil import db, mail
from zembil.models import UserModel, RevokedTokenModel, ShopModel, AdvertisementModel, ProductModel
from zembil.schemas import UserSchema
from zembil.common.util import clean_null_terms

from flask_mail import Message

user_schema = UserSchema()
users_schema = UserSchema(many=True)

user_auth_arguments = reqparse.RequestParser()
user_auth_arguments.add_argument(
    'username', type=str, help="Username", required=True)
user_auth_arguments.add_argument(
    'password', type=str, help="Password", required=True)

auth_reset_arguments = reqparse.RequestParser()
auth_reset_arguments.add_argument(
    'email', type=str, help="Enter your associated email", required=True)
auth_reset_arguments.add_argument(
    'host', type=str, help="Provide the client host address", required=True)

new_passwd_arguments = reqparse.RequestParser()
new_passwd_arguments.add_argument(
    'new_password', type=str, help='Enter new password', required=True)


class Users(Resource):
    @jwt_required()
    def get(self):
        role = get_jwt()['role']
        if role == 'user':
            user_id = get_jwt_identity()
            result = UserModel.query.filter_by(id=user_id).first()
            return user_schema.dump(result)
        users = UserModel.query.all()
        return users_schema.dump(users)

    def post(self):
        data = request.get_json()
        try:
            args = user_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        user = UserModel(
            **args,
            # role="admin"
        )
        db.session.add(user)
        db.session.commit()
        return user_schema.dump(user), 201


class User(Resource):
    @jwt_required()
    def get(self, id):
        result = UserModel.query.filter_by(id=id).first()
        if not result:
            abort(404, message="User not found!")
        return user_schema.dump(result)

    @jwt_required()
    def patch(self, id):
        data = request.get_json()
        try:
            args = UserSchema(partial=True).load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        args = clean_null_terms(args)
        user_id = get_jwt_identity()
        if user_id == id:
            existing = UserModel.query.filter_by(id=id).update(args)
        return abort(403, message="User not authorized!")


class Authorize(Resource):
    def post(self):
        args = user_auth_arguments.parse_args()
        username = args['username']
        password = args['password']
        user = UserModel.query.filter_by(username=username).first()
        if user and user.check_password(password):
            expires = timedelta(days=30)
            additional_claims = {"role": user.role}
            token = create_access_token(
                identity=user.id,
                expires_delta=expires,
                additional_claims=additional_claims)
            return make_response(jsonify({'token': token}))
        return abort(401, message="Incorrect Username or password")


class PasswordReset(Resource):
    def post(self):
        args = auth_reset_arguments.parse_args()
        email = escape(args['email'])
        host = escape(args['host'])
        user = UserModel.query.filter_by(email=email).first()
        if not user:
            return abort(404, message="No user with this email!")

        reset_token = user.get_reset_token(1800)
        full_url = host + '/auth/reset?token=' + reset_token
        try:
            # send emial
            
            msg = Message()
            msg = Message('Password reset token',
                          sender='noreply@zembil.com', 
                          recipients=[user.email])
            # msg.body = f''' To reset your password visit the following link: \n{full_url} \n\nIf you did not send this email then ignore this email.'''
            msg.html = f"""
            Hi {user.name}, <br><br>

            You recently requested to reset the password for your account. Click the link below to proceed.
            <br><br>
            <a href="{full_url}">link</a>
            <br><br>
            If you did not request a password reset, please ignore this email or reply to let us know. This password reset link is only valid for the next 30 minutes.
            <br><br>
            Thanks, the zembil team!
            """
            mail.send(msg)

            return {"message": f"Reset token is sent to {email}"}, 200
        except:
            abort(500, message="Couldn't send an email.")

class VerifyToken(Resource):
    def post(self):
        token = request.args.get('token')
        password = new_passwd_arguments.parse_args()['new_password']
        if not token:
            return abort(400, message="Invalid password reset token!")
        user = UserModel.verify_reset_token(token)
        if user is None:
            return abort(400, message="Invalid or expired password reset token!")

        user.password = password
        db.session.commit()

        return {'message': 'Password reset successful'}, 200


class AdminUser(Resource):
    @jwt_required()
    def post(self):
        role = get_jwt()['role']
        if role == 'user':
            abort(403, message="Admin Privilege Required!")
        data = request.get_json()
        try:
            args = user_schema.load(data)
        except ValidationError as errors:
            abort(400, message=errors.messages)
        user = UserModel(username=args['username'], email=args['email'],
                         password=args['password_hash'], role='admin', phone=args['phone'])
        db.session.add(user)
        db.session.commit()
        return user_schema.dump(user), 201


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            db.session.add(revoked_token)
            db.session.commit()
            return make_response(jsonify({'message': 'User log out succesfull'}), 200)
        except:
            return make_response(jsonify({'message': 'Something went wrong'}), 500)


class AdminStatus(Resource):
    @jwt_required()
    def get(self):
        role = get_jwt()['role']
        if role == 'user':
            abort(403, message="Requires admin privelege")
        product_count = db.session.query(ProductModel).count()
        user_count = db.session.query(UserModel).count()
        advertisement_count = db.session.query(AdvertisementModel).count()
        shop_count = db.session.query(ShopModel).count()
        return make_response(jsonify({
            "products": product_count,
            "users": user_count,
            "ads": advertisement_count,
            "shops": shop_count
        }), 200)
