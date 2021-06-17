from flask import Flask
from flask_jwt_extended.view_decorators import jwt_required
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_restful import abort
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# from flask_wtf.csrf import CSRFProtect
from zembil.config import Config


db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address, 
    default_limits=["5000 per day", "50 per minute"]
)
# csrf = CSRFProtect()
jwt = JWTManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)
    
    CORS(app, supports_credentials=True)
    jwt.init_app(app)
    # csrf.init_app(app)
    limiter.init_app(app)
    db.init_app(app)
    mail.init_app(app)

    from zembil.v1 import api_v1, api_v1_bp, API_VERSION_V1
    
    from zembil.models import RevokedTokenModel
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token = db.session.query(RevokedTokenModel.id).filter_by(jti=jti).scalar()
        return token is not None

    @jwt.unauthorized_loader
    def handle_no_authorization(jwt_header):
        abort(400, message="Authorization header is missing!")
    
    app.register_blueprint(
        api_v1_bp,
        url_prefix='/{prefix}/v{version}'.format(
        prefix='api',
        version=API_VERSION_V1)
    )

    return app
