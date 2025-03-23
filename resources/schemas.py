from marshmallow import Schema, fields

class CartItemSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)  # From Fake Store API
    product_name = fields.Str(required=True)
    product_price = fields.Float(required=True)
    quantity = fields.Int(required=True)

class PlainCartSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    status = fields.Str(required=True)  # "active" or other statuses
    created_at = fields.DateTime(dump_only=True)

    items = fields.List(fields.Nested(CartItemSchema(), dump_only=True))  # List of cart items


class PlainOrderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    cart_id = fields.Int(required=True)
    status = fields.Str(required=True)  # Possible values: "pending", "canceled", "approved"


class CartSchema(PlainCartSchema):
    pass


class OrderSchema(PlainOrderSchema):
    cart = fields.Nested(CartSchema(), dump_only=True)  # Nested cart details for orders


class CartUpdateSchema(Schema):
    status = fields.Str()  # You may want to be able to update the status


class OrderUpdateSchema(Schema):
    status = fields.Str()  # You may want to update order status
