from db import db


class AddressModel(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(400), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("UserModel", back_populates="addresses")
