from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_default_database()

# Define collections
drivers_collection = db["drivers"]
appointments_collection = db["appointments"]
spents_collection = db["spents"]
payments_collection = db["payments"]