from marshmallow import Schema, fields


class PlainCartSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    product_id = fields.Int(required=True)
    product_name = fields.Str(required=True)
    product_price = fields.Float(required=True)


class PlainOrderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    cart_id = fields.Int(required=True)
    status = fields.Str(required=True)  # Possible values: "pending", "canceled", "approved"


class CartSchema(PlainCartSchema):
    pass


class OrderSchema(PlainOrderSchema):
    cart = fields.Nested(PlainCartSchema(), dump_only=True)


class CartUpdateSchema(Schema):
    product_id = fields.Int()
    product_name = fields.Str()
    product_price = fields.Float()


class OrderUpdateSchema(Schema):
    status = fields.Str()
