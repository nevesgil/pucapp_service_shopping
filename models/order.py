from db import db
from datetime import datetime


class OrderModel(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.String(255), nullable=True)
    billing_address = db.Column(db.String(255), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default="unpaid")
    cart = db.relationship("CartModel", back_populates="orders")
    user = db.relationship("UserModel", back_populates="orders")
    items = db.relationship(
        "CartItemModel", secondary="carts", viewonly=True, uselist=True
    )
