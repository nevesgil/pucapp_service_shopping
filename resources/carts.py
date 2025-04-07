from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from models import CartModel, CartItemModel, UserModel, OrderModel
from resources.schemas import (
    CartSchema,
    CartItemSchema,
    CartUpdateSchema,
    OrderSchema,
    CartItemAddSchema,
)
import requests
from db import db
from sqlalchemy import event, text

blp = Blueprint("Carts", __name__, description="Operations on carts")


def calculate_cart_total(cart):
    cart.total_price = sum(item.product_price * item.quantity for item in cart.items)
    return cart


@event.listens_for(CartItemModel, "after_insert")
@event.listens_for(CartItemModel, "after_update")
@event.listens_for(CartItemModel, "after_delete")
def update_cart_total(mapper, connection, target):
    cart = CartModel.query.get(target.cart_id)
    if cart:
        calculate_cart_total(cart)
        db.session.add(cart)
        db.session.commit()


def fetch_item_from_fakestore(product_id):
    try:
        response = requests.get(
            f"https://fakestoreapi.com/products/{product_id}", timeout=5
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            abort(404, message=f"Product {product_id} not found in Fake Store API")
        return {
            "id": data["id"],
            "title": data["title"],
            "price": data["price"],
            "description": data["description"],
            "category": data["category"],
        }
    except requests.Timeout:
        abort(504, message="Request to Fake Store API timed out")
    except requests.RequestException as e:
        abort(
            502,
            message=f"Failed to fetch product {product_id} from Fake Store API: {str(e)}",
        )


@blp.route("/cart")
class CartCreate(MethodView):
    @blp.arguments(CartSchema(exclude=["items"]))
    @blp.response(201, CartSchema)
    def post(self, cart_data):
        """Create a new cart, ensuring the user has only one active cart."""
        user_id = cart_data["user_id"]
        user = UserModel.query.get(user_id)
        if not user:
            user = UserModel(id=user_id)
            db.session.add(user)

        existing_cart = CartModel.query.filter_by(
            user_id=user_id, status="active"
        ).first()
        if existing_cart:
            return existing_cart

        cart = CartModel(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

        return cart


@blp.route("/cart/<int:cart_id>/items")
class CartItemAdd(MethodView):
    @blp.arguments(CartItemAddSchema)
    @blp.response(201, CartItemSchema)
    def post(self, item_data, cart_id):
        """Add item to cart."""
        cart = db.session.execute(
            text("SELECT * FROM carts WHERE id = :cart_id"), {"cart_id": cart_id}
        ).fetchone()

        if not cart:
            abort(404, message="Cart not found")

        product_id = item_data["product_id"]
        quantity = item_data.get("quantity", 1)

        product_data = fetch_item_from_fakestore(product_id)

        if not product_data:
            abort(400, message="Invalid product ID")

        existing_item = db.session.execute(
            text(
                "SELECT * FROM cart_items WHERE cart_id = :cart_id AND product_id = :product_id"
            ),
            {"cart_id": cart_id, "product_id": product_id},
        ).fetchone()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            new_subtotal = new_quantity * product_data["price"]
            db.session.execute(
                text(
                    "UPDATE cart_items SET quantity = :quantity, subtotal = :subtotal WHERE id = :item_id"
                ),
                {
                    "quantity": new_quantity,
                    "subtotal": new_subtotal,
                    "item_id": existing_item.id,
                },
            )
        else:
            db.session.execute(
                text(
                    """
                    INSERT INTO cart_items (cart_id, product_id, product_name, product_price, quantity, subtotal)
                    VALUES (:cart_id, :product_id, :product_name, :product_price, :quantity, :subtotal)
                """
                ),
                {
                    "cart_id": cart_id,
                    "product_id": product_data["id"],
                    "product_name": product_data["title"],
                    "product_price": product_data["price"],
                    "quantity": quantity,
                    "subtotal": product_data["price"] * quantity,
                },
            )

        total_price = (
            db.session.execute(
                text("SELECT SUM(subtotal) FROM cart_items WHERE cart_id = :cart_id"),
                {"cart_id": cart_id},
            ).scalar()
            or 0
        )

        db.session.execute(
            text("UPDATE carts SET total_price = :total_price WHERE id = :cart_id"),
            {"total_price": total_price, "cart_id": cart_id},
        )

        db.session.commit()
        return {"message": "Item added successfully"}, 201


@blp.route("/cart/<int:cart_id>")
class CartManager(MethodView):
    @blp.response(200, CartSchema)
    def get(self, cart_id):
        """Get full cart details."""
        cart = CartModel.query.get_or_404(cart_id)
        return cart

    @blp.arguments(CartUpdateSchema(exclude=["items"]))
    @blp.response(200, CartSchema)
    def put(self, cart_data, cart_id):
        """Update cart status."""
        cart = CartModel.query.get_or_404(cart_id)

        if "status" in cart_data:
            cart.status = cart_data["status"]

            if cart.status == "completed":
                order = OrderModel(
                    user_id=cart.user_id,
                    cart_id=cart.id,
                    status="pending",
                    total_price=cart.total_price,
                    shipping_address="",
                    billing_address="",
                    payment_status="pending",
                )
                db.session.add(order)
                db.session.commit()

        calculate_cart_total(cart)
        db.session.commit()

        return cart

    @blp.response(204)
    def delete(self, cart_id):
        """Delete entire cart and its items using raw SQL queries"""

        cart = db.session.execute(
            text("SELECT id FROM carts WHERE id = :cart_id"), {"cart_id": cart_id}
        ).fetchone()

        if not cart:
            abort(404, message="Cart not found")

        db.session.execute(
            text("DELETE FROM cart_items WHERE cart_id = :cart_id"),
            {"cart_id": cart_id},
        )

        db.session.execute(
            text("DELETE FROM carts WHERE id = :cart_id"), {"cart_id": cart_id}
        )

        db.session.commit()
        return "", 204


@blp.route("/cart/<int:cart_id>/items/<int:product_id>")
class CartItemManager(MethodView):
    def delete(self, cart_id, product_id):
        """Remove specific item from cart using raw SQL queries."""

        item = db.session.execute(
            text(
                "SELECT id FROM cart_items WHERE cart_id = :cart_id AND product_id = :product_id"
            ),
            {"cart_id": cart_id, "product_id": product_id},
        ).fetchone()

        if not item:
            abort(404, message="Item not found in cart")

        db.session.execute(
            text(
                "DELETE FROM cart_items WHERE cart_id = :cart_id AND product_id = :product_id"
            ),
            {"cart_id": cart_id, "product_id": product_id},
        )

        new_total = db.session.execute(
            text(
                "SELECT COALESCE(SUM(subtotal), 0) FROM cart_items WHERE cart_id = :cart_id"
            ),
            {"cart_id": cart_id},
        ).scalar()

        db.session.execute(
            text("UPDATE carts SET total_price = :new_total WHERE id = :cart_id"),
            {"new_total": new_total, "cart_id": cart_id},
        )

        db.session.commit()
        return {"message": "Item removed from cart"}, 200

    @blp.arguments(CartItemSchema(partial=True))
    @blp.response(200, CartItemSchema)
    def patch(self, item_data, cart_id, product_id):
        """Update item quantity using raw SQL queries."""

        item = db.session.execute(
            text(
                "SELECT id, product_price FROM cart_items WHERE cart_id = :cart_id AND product_id = :product_id"
            ),
            {"cart_id": cart_id, "product_id": product_id},
        ).fetchone()

        if not item:
            abort(404, message="Item not found in cart")

        item_id, product_price = item

        if "quantity" in item_data:
            new_quantity = item_data["quantity"]
            new_subtotal = product_price * new_quantity

            db.session.execute(
                text(
                    "UPDATE cart_items SET quantity = :quantity, subtotal = :subtotal WHERE id = :item_id"
                ),
                {
                    "quantity": new_quantity,
                    "subtotal": new_subtotal,
                    "item_id": item_id,
                },
            )

        new_total = db.session.execute(
            text(
                "SELECT COALESCE(SUM(subtotal), 0) FROM cart_items WHERE cart_id = :cart_id"
            ),
            {"cart_id": cart_id},
        ).scalar()

        db.session.execute(
            text("UPDATE carts SET total_price = :new_total WHERE id = :cart_id"),
            {"new_total": new_total, "cart_id": cart_id},
        )

        db.session.commit()

        updated_item = db.session.execute(
            text("SELECT * FROM cart_items WHERE id = :item_id"), {"item_id": item_id}
        ).fetchone()

        updated_item_dict = dict(updated_item._mapping)

        return updated_item_dict


@blp.route("/user/<int:user_id>/carts")
class UserCarts(MethodView):
    @blp.response(200, CartSchema(many=True))
    def get(self, user_id):
        """Retrieve all carts belonging to a user."""
        return CartModel.query.filter_by(user_id=user_id).all()
