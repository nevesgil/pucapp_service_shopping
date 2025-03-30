from db import db
from datetime import datetime


class CartModel(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    total_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    items = db.relationship(
        "CartItemModel", back_populates="cart", cascade="all, delete-orphan"
    )
    user = db.relationship("UserModel", back_populates="carts")
    orders = db.relationship(
        "OrderModel", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItemModel(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)  # From Fake Store API
    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    cart = db.relationship("CartModel", back_populates="items")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subtotal = self.product_price * self.quantity
