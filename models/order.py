from db import db

class OrderModel(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    items = db.relationship("OrderItemModel", back_populates="order", cascade="all, delete-orphan")
    user = db.relationship("UserModel", back_populates="orders")



class OrderItemModel(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)  # From Fake Store API
    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Numeric(10,2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    order = db.relationship("OrderModel", back_populates="items")
