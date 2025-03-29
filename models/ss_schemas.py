from marshmallow import Schema, fields

class CartItemSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)  
    product_name = fields.Str(required=True)
    product_price = fields.Float(required=True)
    quantity = fields.Int(required=True)
    subtotal = fields.Float(dump_only=True)  

class CartItemAddSchema(Schema):
    product_id = fields.Int(required=True)  
    quantity = fields.Int(load_default=1)   

class PlainCartSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    status = fields.Str(required=True, validate=lambda x: x in ["active", "inactive", "completed"])
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    total_price = fields.Float(dump_only=True)
    items = fields.List(fields.Nested(CartItemSchema(), dump_only=True))

class CartUpdateSchema(Schema):
    status = fields.Str(validate=lambda x: x in ["active", "inactive", "completed"])
    items = fields.List(fields.Nested(CartItemSchema()))

class CartSchema(PlainCartSchema):
    pass

class PlainOrderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    cart_id = fields.Int(required=True)
    status = fields.Str(required=True, validate=lambda x: x in ["pending", "canceled", "approved"])
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    total_price = fields.Float(dump_only=True)
    shipping_address = fields.Str()
    billing_address = fields.Str()
    payment_status = fields.Str(dump_only=True)
    
class OrderSchema(PlainOrderSchema):
    cart = fields.Nested(CartSchema(), dump_only=True)
    items = fields.List(fields.Nested(CartItemSchema(), dump_only=True))

class OrderUpdateSchema(Schema):
    status = fields.Str(validate=lambda x: x in ["pending", "canceled", "approved"])
    shipping_address = fields.Str()
    billing_address = fields.Str()