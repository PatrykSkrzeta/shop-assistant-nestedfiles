from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, ReferenceField, ListField, EmbeddedDocument, EmbeddedDocumentField
from flask_login import UserMixin
from datetime import *



class User(UserMixin, Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)

    def get_id(self):
        return self.email


class Product(Document):
    name = StringField(required=True, unique=True)
    category = StringField(required=True)
    product_type = StringField(required=True)
    date_added = DateTimeField(default=lambda: datetime.now(timezone.utc).replace(second=0, microsecond=0))
    value = IntField(required=True)
    price = FloatField(required=True)
    meta = {'collection': 'product'}

class OrderItem(EmbeddedDocument):
    product = ReferenceField(Product, required=True)
    product_name = StringField(required=True)
    quantity = IntField(required=True)
    total_price = FloatField(required=True)
    meta = {'strict': False}

class Order(Document):
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    date_added = DateTimeField(default=lambda: datetime.now(timezone.utc).replace(second=0, microsecond=0))
    pesel = StringField(required=True)
    contact = StringField(required=True)
    address = StringField(required=True)
    order_items = ListField(EmbeddedDocumentField(OrderItem), required=True)
    total_order_price = FloatField(required=True)
    discount = FloatField(default=0)
    meta = {'collection': 'order'}



