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
    status = fields.Str(required=True, validate=lambda x: x in ["active", "inactive", "completed"])  # Validation for status
    created_at = fields.DateTime(dump_only=True)

    items = fields.List(fields.Nested(CartItemSchema(), dump_only=True))  # List of cart items


class PlainOrderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    cart_id = fields.Int(required=True)
    status = fields.Str(required=True, validate=lambda x: x in ["pending", "canceled", "approved"])  # Validation for status


class CartSchema(PlainCartSchema):
    pass


class OrderSchema(PlainOrderSchema):
    cart = fields.Nested(CartSchema(), dump_only=True)  # Nested cart details for orders
    items = fields.List(fields.Nested(CartItemSchema(), dump_only=True))  # Optionally include cart items in order response


class CartUpdateSchema(Schema):
    status = fields.Str(validate=lambda x: x in ["active", "inactive", "completed"])  # Validation for status
    items = fields.List(fields.Nested(CartItemSchema()))  # Allow updating cart items


class OrderUpdateSchema(Schema):
    status = fields.Str(validate=lambda x: x in ["pending", "canceled", "approved"])  # Validation for status
