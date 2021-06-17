from flask import Blueprint
from flask_restful import Api
from flask_cors import CORS
import zembil.resources.v1.user as user
import zembil.resources.v1.shop as shop
import zembil.resources.v1.category as category
import zembil.resources.v1.location as location
import zembil.resources.v1.shopfollow as shopfollow
import zembil.resources.v1.review as review
import zembil.resources.v1.wishlist as wishlist
import zembil.resources.v1.product as product
import zembil.resources.v1.advertisement as ads
import zembil.resources.v1.upload as upload
import zembil.resources.v1.notification as notification

API_VERSION_V1 = 1
API_VERSION = API_VERSION_V1
api_v1_bp = Blueprint('api_v1', __name__)
CORS(api_v1_bp, supports_credentials=True)
api_v1 = Api(api_v1_bp)

api_v1.add_resource(user.Users, '/users')
api_v1.add_resource(user.User, '/users/<int:id>')
api_v1.add_resource(user.Authorize, '/auth')
api_v1.add_resource(user.UserLogout, '/users/logout')
api_v1.add_resource(user.AdminUser, '/admin')
api_v1.add_resource(user.AdminStatus, '/admin/status')
api_v1.add_resource(notification.Notification, '/users/notification')
api_v1.add_resource(shop.UserShops, '/users/shops')

api_v1.add_resource(user.PasswordReset, '/auth/forgot')
api_v1.add_resource(user.VerifyToken, '/auth/reset')

api_v1.add_resource(category.Categories, '/categories')
api_v1.add_resource(category.Category, '/categories/<int:id>')

api_v1.add_resource(location.Locations, '/locations')
api_v1.add_resource(location.Location, '/locations/<int:id>')

api_v1.add_resource(shop.Shops, '/shops')
api_v1.add_resource(shop.Shop, '/shops/<int:id>')
api_v1.add_resource(product.ShopProducts, '/shops/<int:shop_id>/products')
api_v1.add_resource(product.UserProducts, '/shops/products')
api_v1.add_resource(shop.ApproveShop, '/shops/<int:id>/status')
api_v1.add_resource(shopfollow.ShopFollowers, '/shops/<int:shopid>/followers', methods=['GET', 'POST', 'DELETE'])
api_v1.add_resource(upload.UploadShopImage, '/shops/<int:shop_id>/uploads')

api_v1.add_resource(review.Reviews, '/products/<int:product_id>/reviews')
api_v1.add_resource(
    review.Review, '/products/<int:product_id>/reviews/<int:id>')
api_v1.add_resource(product.Products, '/products')
api_v1.add_resource(product.Product, '/products/<int:id>')
api_v1.add_resource(product.TrendingProduct, '/products/trending')
api_v1.add_resource(upload.UploadProductImage,
                    '/products/<int:product_id>/uploads')

api_v1.add_resource(product.FilterProduct, '/filter/products')
api_v1.add_resource(product.SearchProduct, '/search/products')
api_v1.add_resource(shop.SearchShop, '/search/shops')
api_v1.add_resource(location.LocationNearMe, '/search/shops/nearme')

api_v1.add_resource(wishlist.WishList, '/cart/<int:id>')
api_v1.add_resource(wishlist.WishLists, '/cart')

api_v1.add_resource(ads.Advertisements, '/ads')
api_v1.add_resource(ads.Advertisement, '/ads/<int:id>')
