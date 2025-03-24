from db import db
from datetime import datetime

class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    carts = db.relationship("CartModel", back_populates="user")
    orders = db.relationship("OrderModel", back_populates="user")