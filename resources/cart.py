from flask.views import MethodView
from flask_smorest import abort, Blueprint
from db import db
from models import CartModel, CartItemModel
from resources.schemas import CartSchema, CartUpdateSchema, PlainCartSchema

blp = Blueprint("Carts", __name__, description="Operations on carts")

@blp.route("/cart/<int:cart_id>")
class Cart(MethodView):
    @blp.response(200, CartSchema)
    def get(self, cart_id):
        """Retrieve a cart by ID"""
        return CartModel.query.get_or_404(cart_id)

    @blp.arguments(CartUpdateSchema)
    @blp.response(200, CartSchema)
    def put(self, cart_data, cart_id):
        """Update a cart"""
        cart = CartModel.query.get(cart_id)
        if not cart:
            abort(404, message="Cart not found")

        # Update the cart information as needed
        for key, value in cart_data.items():
            setattr(cart, key, value)

        db.session.commit()
        return cart

    def delete(self, cart_id):
        """Delete a cart"""
        cart = CartModel.query.get(cart_id)
        if not cart:
            abort(404, message="Cart not found")
        db.session.delete(cart)
        db.session.commit()
        return {"message": "Cart deleted successfully"}, 200


@blp.route("/cart")
class CartList(MethodView):
    @blp.response(200, CartSchema(many=True))
    def get(self):
        """Retrieve all carts"""
        return CartModel.query.all()

    @blp.arguments(PlainCartSchema)
    @blp.response(201, CartSchema)
    def post(self, cart_data):
        """Create a new cart"""
        cart = CartModel(**cart_data)
        db.session.add(cart)
        db.session.commit()
        return cart, 201


@blp.route("/cart/<int:cart_id>/item")
class CartItem(MethodView):
    @blp.arguments(CartUpdateSchema)
    @blp.response(201, CartSchema)
    def post(self, cart_data, cart_id):
        """Add an item to a cart"""
        cart = CartModel.query.get(cart_id)
        if not cart:
            abort(404, message="Cart not found")

        cart_item = CartItemModel(cart_id=cart_id, **cart_data)
        db.session.add(cart_item)
        db.session.commit()
        return cart_item, 201


@blp.route("/cart/<int:cart_id>/item/<int:item_id>")
class CartItemDetail(MethodView):
    @blp.arguments(CartUpdateSchema)
    @blp.response(200, CartSchema)
    def put(self, cart_data, cart_id, item_id):
        """Update the item in the cart"""
        cart_item = CartItemModel.query.get(item_id)
        if not cart_item or cart_item.cart_id != cart_id:
            abort(404, message="Item not found in this cart")

        for key, value in cart_data.items():
            setattr(cart_item, key, value)

        db.session.commit()
        return cart_item

    def delete(self, cart_id, item_id):
        """Delete an item from the cart"""
        cart_item = CartItemModel.query.get(item_id)
        if not cart_item or cart_item.cart_id != cart_id:
            abort(404, message="Item not found in this cart")
        db.session.delete(cart_item)
        db.session.commit()
        return {"message": "Item deleted successfully"}, 200
