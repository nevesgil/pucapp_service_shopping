from flask.views import MethodView
from flask_smorest import abort, Blueprint
from sqlalchemy.exc import SQLAlchemyError
from db import db
from models import OrderModel, CartModel
from resources.schemas import OrderSchema, OrderUpdateSchema
from datetime import datetime
from sqlalchemy import text

blp = Blueprint("Orders", __name__, description="Operations on orders")

def calculate_order_total(cart):
    return sum(item.product_price * item.quantity for item in cart.items)

@blp.route("/order/<int:order_id>")
class Order(MethodView):
    @blp.response(200, OrderSchema)
    def get(self, order_id):
        """Retrieve order details with cart snapshot"""
        order = OrderModel.query.get_or_404(order_id)
        return order

    @blp.arguments(OrderUpdateSchema)
    @blp.response(200, OrderSchema)
    def put(self, order_data, order_id):
        """Update order status/shipping details"""
        order = OrderModel.query.get_or_404(order_id)
        
        if "status" in order_data:
            if order.status == 'completed' and order_data["status"] != 'completed':
                abort(400, message="Completed orders cannot be modified")
            order.status = order_data["status"]

            if order_data["status"] == 'canceled':
                cart_id = db.session.execute(
                    text("SELECT cart_id FROM orders WHERE id = :order_id"), {"order_id": order_id}
                ).fetchone()

                if cart_id and cart_id[0]:
                    # Update cart status to inactive
                    db.session.execute(
                        text("UPDATE carts SET status = 'inactive' WHERE id = :cart_id"), {"cart_id": cart_id[0]}
                    )
        # Update shipping/billing info if provided
        for field in ['shipping_address', 'billing_address', 'payment_status']:
            if field in order_data:
                setattr(order, field, order_data[field])
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return order

    @blp.response(204)
    def delete(self, order_id):
        """Cancel an order (if allowed)"""
        order = OrderModel.query.get_or_404(order_id)
        
        if order.status == 'completed':
            abort(400, message="Completed orders cannot be deleted")
            
        db.session.delete(order)
        db.session.commit()
        return ""

@blp.route("/order")
class OrderList(MethodView):
    @blp.response(200, OrderSchema(many=True))
    def get(self):
        """List all orders"""
        return OrderModel.query.all()

    @blp.arguments(OrderSchema(exclude=["status", "payment_status"]))
    @blp.response(201, OrderSchema)
    def post(self, order_data):
        """Create new order from cart"""
        cart = CartModel.query.get(order_data["cart_id"])
        
        # Validation checks
        if not cart:
            abort(404, message="Cart not found")
        if cart.user_id != order_data["user_id"]:
            abort(403, message="Cart does not belong to this user")
        if not cart.items:
            abort(400, message="Cannot create order from empty cart")
        if cart.status != 'active':
            abort(400, message="Cart is not active for ordering")

        try:
            # Create order with cart snapshot
            order = OrderModel(
                user_id=order_data["user_id"],
                cart_id=cart.id,
                total_price=calculate_order_total(cart),
                shipping_address=order_data.get("shipping_address"),
                billing_address=order_data.get("billing_address")
            )

            # Freeze cart state by updating its status
            cart.status = "ordered"
            
            db.session.add(order)
            db.session.commit()
            return order
            
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, message="Error creating order")

@blp.route("/user/<int:user_id>/orders")
class UserOrders(MethodView):
    @blp.response(200, OrderSchema(many=True))
    def get(self, user_id):
        """Retrieve all orders placed by a user."""
        orders = OrderModel.query.filter_by(user_id=user_id).all()
        return orders