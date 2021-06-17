from flask_restful import Resource, abort
from flask_jwt_extended import ( jwt_required, get_jwt_identity)
from zembil import db
from zembil.models import NotificationModel
from zembil.schemas import NotificationSchema

notifications_schema = NotificationSchema(many=True)

class Notification(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        notification = NotificationModel.query.filter_by(id=user_id)
        if notification and notification.first().user_id == user_id:
            notification.update({"seen": True})
            db.session.commit()
            return notifications_schema.dump(notification.all())
        abort(404, message="Notification not found!")

    @jwt_required()
    def delete(self):
        user_id = get_jwt_identity()
        db.session.query(NotificationModel) \
            .filter(NotificationModel.user_id == user_id) \
            .delete(synchronize_session=False)
        return 200

      
