from flask.views import MethodView
from flask_smorest import abort, Blueprint
from db import db
from models import CartModel, CartItemModel
from sqlalchemy.exc import SQLAlchemyError
from resources.schemas import CartSchema, CartItemSchema, CartItemUpdateSchema

blp = Blueprint("Carts", __name__, description="Operations on carts")


@blp.route("/cart/<int:user_id>")
class Cart(MethodView):
    @blp.response(200, CartSchema)
    def get(self, user_id):
        """Retrieve the cart for a specific user"""
        cart = CartModel.query.filter_by(user_id=user_id, is_active=True).first()
        if not cart:
            abort(404, message="Cart not found")
        return cart

    def delete(self, user_id):
        """Clear the user's cart"""
        cart = CartModel.query.filter_by(user_id=user_id, is_active=True).first_or_404()
        db.session.delete(cart)
        db.session.commit()
        return {"message": "Cart cleared"}, 200


@blp.route("/cart/<int:user_id>/items")
class CartItems(MethodView):
    @blp.response(200, CartItemSchema(many=True))
    def get(self, user_id):
        """Retrieve all items in the user's cart"""
        cart = CartModel.query.filter_by(user_id=user_id, is_active=True).first_or_404()
        return cart.items  # Assuming `items` is a relationship in CartModel

    @blp.arguments(CartItemSchema)
    @blp.response(201, CartItemSchema)
    def post(self, item_data, user_id):
        """Add an item to the user's cart"""
        cart = CartModel.query.filter_by(user_id=user_id, is_active=True).first()
        if not cart:
            cart = CartModel(user_id=user_id, is_active=True)
            db.session.add(cart)
            db.session.commit()

        item = CartItemModel(cart_id=cart.id, **item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Error adding item to cart")

        return item, 201


@blp.route("/cart/<int:user_id>/items/<int:item_id>")
class CartItem(MethodView):
    def delete(self, user_id, item_id):
        """Remove an item from the user's cart"""
        item = CartItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item removed from cart"}, 200

    @blp.arguments(CartItemUpdateSchema)
    @blp.response(200, CartItemSchema)
    def put(self, item_data, user_id, item_id):
        """Update an item in the user's cart (e.g., change quantity)"""
        item = CartItemModel.query.get_or_404(item_id)
        
        for key, value in item_data.items():
            setattr(item, key, value)

        db.session.commit()
        return item
