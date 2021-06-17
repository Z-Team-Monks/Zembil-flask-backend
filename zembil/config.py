import os


class Config:
    SECRET_KEY = '5791628bb0b13ce0c676dfde280ba245'
    JWT_SECRET_KEY = '5791628bb0b13ce0c676dfde280ba245'
    JWT_BLACKLIST_ENABLED = ['access']
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password1@localhost:5432/zembilflask'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = './zembil/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    CORS_HEADERS = 'Content-Type'
    PAGINATION_PAGE_SIZE = 9
    PAGINATION_PAGE_ARGUMENT_NAME = 'page'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "team.zembil@gmail.com"
    MAIL_PASSWORD = "zembiltest123"
    PROPAGATE_EXCEPTIONS = True
