from flask import Flask
from mongoengine import connect

app = Flask(__name__)

# Połącz się z bazą danych MongoDB
connect('shopassistant')

# Usuń wszystkie indeksy z kolekcji `product`
from mongoengine.connection import get_db
from models import Order
# Pobranie wszystkich dokumentów z kolekcji Order


# Wyświetlenie każdego dokumentu w bardziej czytelnej formie
Order.objects().delete()

print("All documents in the 'Order' collection have been deleted.")

print("All indexes except _id have been dropped.")