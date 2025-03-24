from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from marshmallow import ValidationError
from models import CartModel, CartItemModel
from resources.schemasv1 import CartSchema, CartItemSchema
import requests
from db import db

blp = Blueprint("Carts", __name__, description="Operations on carts")


def fetch_item_from_fakestore(product_id):
    """Fetch item details from Fake Store API."""
    try:
        response = requests.get(f"https://fakestoreapi.com/products/{product_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


@blp.route("/cart")
class Cart(MethodView):
    @blp.arguments(CartSchema)
    @blp.response(201, CartSchema)
    def post(self, cart_data):
        """Create a new cart with items fetched from the Fake Store API and set quantities."""
        items_data = cart_data.get("items", [])
        cart = CartModel(user_id=cart_data["user_id"])

        for item_data in items_data:
            product_data = fetch_item_from_fakestore(item_data["product_id"])
            if product_data:
                cart_item = CartItemModel(
                    cart_id=cart.id,
                    product_id=product_data["id"],
                    product_name=product_data["title"],
                    product_price=product_data["price"],
                    quantity=item_data.get("quantity", 1)
                )
                cart.items.append(cart_item)
            else:
                abort(400, message=f"Item {item_data['product_id']} could not be fetched from the Fake Store API.")

        db.session.add(cart)
        db.session.commit()
        return cart, 201


#### 2. Update a Cart (Add/Remove/Modify Cart Items)


@blp.route("/cart/<int:cart_id>")
class CartUpdate(MethodView):
    @blp.arguments(CartSchema)
    @blp.response(200, CartSchema)
    def put(self, cart_data, cart_id):
        """Update an existing cart (add/remove items, change quantities)."""
        cart = CartModel.query.get_or_404(cart_id)

        # Update cart details
        if "status" in cart_data:
            cart.status = cart_data["status"]

        # Update items in cart
        for item_data in cart_data.get("items", []):
            # Check if the item exists in the cart
            item = CartItemModel.query.filter_by(cart_id=cart.id, product_id=item_data["product_id"]).first()

            if item:
                # Update item quantity
                item.quantity = item_data.get("quantity", item.quantity)
            else:
                # Add new item if not found in the cart
                product_data = fetch_item_from_fakestore(item_data["product_id"])
                if product_data:
                    new_item = CartItemModel(
                        cart_id=cart.id,
                        product_id=product_data["id"],
                        product_name=product_data["title"],
                        product_price=product_data["price"],
                        quantity=item_data.get("quantity", 1)
                    )
                    cart.items.append(new_item)

        db.session.commit()
        return cart


#### 3. Delete a Cart (Remove All Items and Cart)


@blp.route("/cart/<int:cart_id>")
class CartDelete(MethodView):
    def delete(self, cart_id):
        """Delete a cart and all its items."""
        cart = CartModel.query.get_or_404(cart_id)

        try:
            db.session.delete(cart)
            db.session.commit()
            return {"message": "Cart deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            abort(500, message="Error deleting cart")


@blp.route("/cart/<int:cart_id>")
class CartDetail(MethodView):
    @blp.response(200, CartSchema)
    def get(self, cart_id):
        """Get a user's cart with full details of the items in the cart."""
        cart = CartModel.query.get_or_404(cart_id)

        # Serialize cart items
        cart_items = []
        for item in cart.items:
            product_data = fetch_item_from_fakestore(item.product_id)
            if product_data:
                cart_items.append({
                    "product_id": item.product_id,
                    "product_name": product_data["title"],
                    "product_price": product_data["price"],
                    "quantity": item.quantity,
                    "product_description": product_data["description"],
                    "product_image": product_data["image"]
                })

        return {
            "id": cart.id,
            "user_id": cart.user_id,
            "status": cart.status,
            "created_at": cart.created_at,
            "items": cart_items
        }


@blp.route("/product/<int:product_id>")
class Product(MethodView):
    def get(self, product_id):
        """Get a single product's full details from the Fake Store API."""
        product_data = fetch_item_from_fakestore(product_id)
        
        if product_data:
            return product_data
        else:
            abort(404, message="Product not found")
