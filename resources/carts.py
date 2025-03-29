from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from models import CartModel, CartItemModel, UserModel, OrderModel
from models.ss_schemas import CartSchema, CartItemSchema, CartUpdateSchema, OrderSchema, CartItemAddSchema
import requests
from db import db
from sqlalchemy import event

blp = Blueprint("Carts", __name__, description="Operations on carts")

def calculate_cart_total(cart):
    cart.total_price = sum(item.product_price * item.quantity for item in cart.items)
    return cart

# SQLAlchemy event to update cart total when items change
@event.listens_for(CartItemModel, 'after_insert')
@event.listens_for(CartItemModel, 'after_update')
@event.listens_for(CartItemModel, 'after_delete')
def update_cart_total(mapper, connection, target):
    cart = CartModel.query.get(target.cart_id)
    if cart:
        calculate_cart_total(cart)
        db.session.add(cart)
        db.session.commit()

def fetch_item_from_fakestore(product_id):
    try:
        response = requests.get(f"https://fakestoreapi.com/products/{product_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            abort(404, message=f"Product {product_id} not found in Fake Store API")
        return {
            "id": data["id"],
            "title": data["title"],
            "price": data["price"],
            "description": data["description"],
            "category": data["category"]
        }
    except requests.Timeout:
        abort(504, message="Request to Fake Store API timed out")  # Return proper error
    except requests.RequestException as e:
        abort(502, message=f"Failed to fetch product {product_id} from Fake Store API: {str(e)}")


@blp.route("/cart")
class CartCreate(MethodView):
    @blp.arguments(CartSchema(exclude=["items"]))  # Exclude items during cart creation
    @blp.response(201, CartSchema)
    def post(self, cart_data):
        """Create a new cart, ensuring the user has only one active cart. Optionally, add a product to the cart."""
        user_id = cart_data["user_id"]
        user = UserModel.query.get(user_id)
        if not user:
            user = UserModel(id=user_id)
            db.session.add(user)

        # Ensure there is only one active cart per user
        existing_cart = CartModel.query.filter_by(user_id=user_id, status="active").first()
        if existing_cart:
            return existing_cart  # Prevent multiple active carts

        # Create a new cart for the user
        cart = CartModel(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

        # Check if a product ID and quantity were provided in the request to add an item to the cart
        if "product_id" in cart_data:
            product_id = cart_data["product_id"]
            quantity = cart_data.get("quantity", 1)

            # Fetch product details from the Fake Store API
            product_data = fetch_item_from_fakestore(product_id)
            if product_data:
                new_item = CartItemModel(
                    cart_id=cart.id,
                    product_id=product_data["id"],
                    product_name=product_data["title"],
                    product_price=product_data["price"],
                    quantity=quantity
                )
                cart.items.append(new_item)
                calculate_cart_total(cart)

                db.session.commit()

        return cart

@blp.route("/cart/<int:cart_id>")
class CartManager(MethodView):
    @blp.response(200, CartSchema)
    def get(self, cart_id):
        """Get full cart details."""
        cart = CartModel.query.get_or_404(cart_id)
        return cart  # Let Marshmallow schema handle serialization

    @blp.arguments(CartUpdateSchema)
    @blp.response(200, CartSchema)
    def put(self, cart_data, cart_id):
        """Update cart status."""
        cart = CartModel.query.get_or_404(cart_id)
        
        # Update status if provided
        if "status" in cart_data:
            cart.status = cart_data["status"]
            
            # If the status is completed, create an order for the cart
            if cart.status == "completed":
                order = OrderModel(
                    user_id=cart.user_id,
                    cart_id=cart.id,
                    status="pending",  # Order starts as pending
                    total_price=cart.total_price,
                    shipping_address="",
                    billing_address="",
                    payment_status="pending"  # You can adjust the default payment status as needed
                )
                db.session.add(order)
                db.session.commit()

        # Recalculate the cart total after status change
        calculate_cart_total(cart)
        db.session.commit()
        
        return cart

    @blp.response(204)
    def delete(self, cart_id):
        """Delete entire cart"""
        cart = CartModel.query.get_or_404(cart_id)
        
        # Delete associated cart items first
        for item in cart.items:
            db.session.delete(item)
        
        db.session.delete(cart)
        db.session.commit()
        return "", 204

@blp.route("/cart/<int:cart_id>/items")
class CartItemAdd(MethodView):
    @blp.arguments(CartItemAddSchema)
    @blp.response(201, CartItemSchema)
    def post(self, item_data, cart_id):
        cart = CartModel.query.get_or_404(cart_id)
        
        product_id = item_data["product_id"]
        quantity = item_data.get("quantity", 1)

        # Fetch product details from the Fake Store API
        product_data = fetch_item_from_fakestore(product_id)
        
        if product_data:
            # Check for existing item
            existing_item = next((item for item in cart.items if item.product_id == product_id), None)
            print("jajajajajaja")
            
            if existing_item:
                # Update quantity if item already exists
                existing_item.quantity += quantity
                existing_item.update_subtotal()
            else:
                print("this part")
                # Create new item if it doesn't exist
                new_item = CartItemModel(
                    cart_id=cart.id,
                    product_id=product_data["id"],
                    product_name=product_data["title"],
                    product_price=product_data["price"],
                    quantity=quantity
                )
                cart.items.append(new_item)

            calculate_cart_total(cart)
            db.session.commit()
            
            return new_item if not existing_item else existing_item, 201
        
        abort(400, message="Invalid product ID")

@blp.route("/cart/<int:cart_id>/items/<int:product_id>")
class CartItemManager(MethodView):
    def delete(self, cart_id, product_id):
        """Remove specific item from cart."""
        item = CartItemModel.query.filter_by(cart_id=cart_id, product_id=product_id).first()
        
        # Check if item exists
        if not item:
            abort(404, message="Item not found in cart")
        
        # Remove item from the cart
        db.session.delete(item)
        db.session.commit()
        
        # Recalculate the cart total after item removal
        cart = CartModel.query.get(cart_id)
        if cart:
            calculate_cart_total(cart)
        
        db.session.commit()
        
        return {"message": "Item removed from cart"}, 200

    @blp.arguments(CartItemSchema(partial=True))  # Supports partial updates
    @blp.response(200, CartItemSchema)
    def patch(self, item_data, cart_id, product_id):
        """Update item quantity."""
        item = CartItemModel.query.filter_by(cart_id=cart_id, product_id=product_id).first()
        
        # Check if item exists
        if not item:
            abort(404, message="Item not found in cart")
        
        # Update quantity if provided
        if "quantity" in item_data:
            item.quantity = item_data["quantity"]
            item.update_subtotal()  # This updates the subtotal for the item
        
        # Recalculate the cart total after the quantity change
        cart = CartModel.query.get(cart_id)
        if cart:
            calculate_cart_total(cart)
        
        db.session.commit()
        return item

@blp.route("/user/<int:user_id>/carts")
class UserCarts(MethodView):
    @blp.response(200, CartSchema(many=True))
    def get(self, user_id):
        """Retrieve all carts belonging to a user."""
        return CartModel.query.filter_by(user_id=user_id).all()
