from marshmallow import Schema, fields


class PlainUserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    birthdate = fields.Date(required=True)


class PlainAddressSchema(Schema):
    id = fields.Int(dump_only=True)
    street = fields.Str(required=False)  # street is not required during creation, filled by ViaCEP
    city = fields.Str(required=False)  # city is not required during creation, filled by ViaCEP
    state = fields.Str(required=False)  # state is not required during creation, filled by ViaCEP
    zip_code = fields.Str(required=True)  # only zip_code is required at creation
    country = fields.Str(required=False)  # country is not required during creation, filled by ViaCEP


class UserSchema(PlainUserSchema):
    addresses = fields.List(fields.Nested(PlainAddressSchema(), dump_only=True))


class AddressSchema(PlainAddressSchema):
    user_id = fields.Int(load_only=True)  # user_id should be supplied when creating an address
    user = fields.Nested(PlainUserSchema(), dump_only=True)


class UserUpdateSchema(Schema):
    name = fields.Str()
    birthdate = fields.Date()


class AddressUpdateSchema(Schema):
    street = fields.Str()
    city = fields.Str()
    state = fields.Str()
    zip_code = fields.Str()
    country = fields.Str()
