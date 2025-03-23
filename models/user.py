from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    birthdate = db.Column(db.Date, nullable=False)

    #
    addresses = db.relationship(
        "AddressModel", back_populates="user", cascade="all, delete-orphan"
    )
