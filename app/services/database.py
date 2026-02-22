import os
import motor.motor_asyncio
import logging

logger = logging.getLogger(__name__)

MONGO_URI   = os.getenv("MONGO_URI","mongodb://localhost:27017")
DATABASE    = os.getenv("MONGO_DATABASE","insurance_db")
COLLECTION  = os.getenv("MONGO_COLLECTION","jewellers_quote")


class Database:
    def __init__(self):
        print(f"DEBUG MONGO_URI='{MONGO_URI}'")
        self.client     = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self.database   = self.client[DATABASE]
        self.collection = self.database[COLLECTION]
        logger.info(f"MongoDB connected | DB: {DATABASE} | Collection: {COLLECTION}")


db = Database()
