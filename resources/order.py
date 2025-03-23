from flask.views import MethodView
from flask_smorest import abort, Blueprint
from db import db
from models import OrderModel, OrderItemModel, CartModel
from resources.schemas import OrderSchema, OrderUpdateSchema, PlainOrderSchema

blp = Blueprint("Orders", __name__, description="Operations on orders")


@blp.route("/order/<int:order_id>")
class Order(MethodView):
    @blp.response(200, OrderSchema)
    def get(self, order_id):
        """Retrieve an order by ID"""
        return OrderModel.query.get_or_404(order_id)

    @blp.arguments(OrderUpdateSchema)
    @blp.response(200, OrderSchema)
    def put(self, order_data, order_id):
        """Update an existing order"""
        order = OrderModel.query.get(order_id)
        if not order:
            abort(404, message="Order not found")

        if "status" in order_data:
            order.status = order_data["status"]

        db.session.commit()
        return order

    def delete(self, order_id):
        """Delete an order"""
        order = OrderModel.query.get(order_id)
        if not order:
            abort(404, message="Order not found")
        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted successfully"}, 200


@blp.route("/order")
class OrderList(MethodView):
    @blp.response(200, OrderSchema(many=True))
    def get(self):
        """Retrieve all orders"""
        return OrderModel.query.all()

    @blp.arguments(PlainOrderSchema)
    @blp.response(201, OrderSchema)
    def post(self, order_data):
        """Create a new order"""
        # Ensure the cart exists before creating an order
        cart = CartModel.query.get(order_data["cart_id"])
        if not cart:
            abort(404, message="Cart not found")
        
        # Create the order linked to the existing cart
        order = OrderModel(**order_data)
        db.session.add(order)
        db.session.commit()

        # Optionally, create order items (if required, based on the cart items)
        for item in cart.items:
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_price=item.product_price,
                quantity=item.quantity,
            )
            db.session.add(order_item)

        db.session.commit()
        return order, 201
