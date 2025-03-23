from flask.views import MethodView
from flask_smorest import abort, Blueprint
from db import db
from models import OrderModel
from sqlalchemy.exc import SQLAlchemyError
from resources.schemas import OrderSchema, OrderUpdateSchema

blp = Blueprint("Orders", __name__, description="Operations on orders")


@blp.route("/order/<int:order_id>")
class Order(MethodView):
    @blp.response(200, OrderSchema)
    def get(self, order_id):
        """Retrieve an order by ID"""
        return OrderModel.query.get_or_404(order_id)

    def delete(self, order_id):
        """Delete an order by ID"""
        order = OrderModel.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted successfully"}, 200

    @blp.arguments(OrderUpdateSchema)
    @blp.response(200, OrderSchema)
    def put(self, order_data, order_id):
        """Update an order status"""
        order = OrderModel.query.get_or_404(order_id)

        if "status" in order_data:
            order.status = order_data["status"]

        db.session.commit()
        return order


@blp.route("/order")
class OrderList(MethodView):
    @blp.response(200, OrderSchema(many=True))
    def get(self):
        """Retrieve all orders"""
        return OrderModel.query.all()

    @blp.arguments(OrderSchema)
    @blp.response(201, OrderSchema)
    def post(self, order_data):
        """Create a new order from cart items"""
        order = OrderModel(**order_data)

        try:
            db.session.add(order)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Error inserting the order")

        return order, 201
