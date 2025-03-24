from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from models import CartModel, CartItemModel, UserModel
from resources.schemas import CartSchema, CartItemSchema, CartUpdateSchema
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
        return response.json()
    except requests.RequestException as e:
        abort(502, message=f"Failed to fetch product {product_id} from Fake Store API")

def fetch_all_products():
    """Fetch all products from Fake Store API."""
    try:
        response = requests.get("https://fakestoreapi.com/products")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

@blp.route("/products")
class ProductList(MethodView):
    def get(self):
        """Fetch all available products from the Fake Store API."""
        products = fetch_all_products()
        if products:
            return products
        else:
            abort(500, message="Failed to fetch products from Fake Store API")

@blp.route("/cart/<int:cart_id>")
class CartDetail(MethodView):
    @blp.response(200, CartSchema)
    def get(self, cart_id):
        """Retrieve a cart's details including fetched product info."""
        cart = CartModel.query.get_or_404(cart_id)

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

@blp.route("/cart")
class CartCreate(MethodView):
    @blp.arguments(CartSchema(exclude=["items"]))  # Exclude items during creation
    @blp.response(201, CartSchema)
    def post(self, cart_data):
        """Create a new empty cart for a user."""
        # Check if the user exists
        user_id = cart_data["user_id"]
        user = UserModel.query.filter_by(id=user_id).first()

        # Dynamically create the user if not found
        if not user:
            user = UserModel(id=user_id)
            db.session.add(user)

        # Create a new cart for the user
        cart = CartModel(user_id=user_id)
        
        db.session.add(cart)
        db.session.commit()
        return cart


@blp.route("/cart/<int:cart_id>")
class CartManager(MethodView):
    @blp.response(200, CartSchema)
    def get(self, cart_id):
        """Get full cart details"""
        cart = CartModel.query.get_or_404(cart_id)
        return cart  # Let Marshmallow schema handle serialization

    @blp.arguments(CartUpdateSchema)
    @blp.response(200, CartSchema)
    def put(self, cart_data, cart_id):
        """Update cart items and status"""
        cart = CartModel.query.get_or_404(cart_id)
        
        # Update status if provided
        if "status" in cart_data:
            cart.status = cart_data["status"]
        
        # Process item updates
        if "items" in cart_data:
            current_items = {item.product_id: item for item in cart.items}
            
            for item_data in cart_data["items"]:
                product_id = item_data["product_id"]
                
                if product_id in current_items:
                    # Update existing item
                    item = current_items[product_id]
                    item.quantity = item_data.get("quantity", item.quantity)
                else:
                    # Add new item
                    product_data = fetch_item_from_fakestore(product_id)
                    new_item = CartItemModel(
                        cart_id=cart.id,
                        product_id=product_data["id"],
                        product_name=product_data["title"],
                        product_price=product_data["price"],
                        quantity=item_data.get("quantity", 1)
                    )
                    cart.items.append(new_item)
            
            # Remove items not in update data
            updated_ids = {item["product_id"] for item in cart_data["items"]}
            for product_id in list(current_items.keys()):
                if product_id not in updated_ids:
                    db.session.delete(current_items[product_id])
        
        calculate_cart_total(cart)
        db.session.commit()
        return cart

    @blp.response(204)
    def delete(self, cart_id):
        """Delete entire cart"""
        cart = CartModel.query.get_or_404(cart_id)
        db.session.delete(cart)
        db.session.commit()
        return ""

@blp.route("/cart/<int:cart_id>/items/<int:product_id>")
class CartItemManager(MethodView):
    def delete(self, cart_id, product_id):
        """Remove specific item from cart"""
        cart = CartModel.query.get_or_404(cart_id)
        item = CartItemModel.query.filter_by(cart_id=cart_id, product_id=product_id).first()
        
        if not item:
            abort(404, message="Item not found in cart")
            
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item removed from cart"}, 200

    @blp.arguments(CartItemSchema(only=["quantity"]))
    @blp.response(200, CartItemSchema)
    def patch(self, item_data, cart_id, product_id):
        """Update item quantity"""
        item = CartItemModel.query.filter_by(cart_id=cart_id, product_id=product_id).first()
        
        if not item:
            abort(404, message="Item not found in cart")
            
        item.quantity = item_data.get("quantity", item.quantity)
        db.session.commit()
        return item


@blp.route("/user/<int:user_id>/carts")
class UserCarts(MethodView):
    @blp.response(200, CartSchema(many=True))
    def get(self, user_id):
        """Retrieve all carts belonging to a user."""
        carts = CartModel.query.filter_by(user_id=user_id).all()
        return carts
    
