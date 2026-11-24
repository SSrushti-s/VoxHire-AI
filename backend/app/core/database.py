
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = None
database = None


async def connect_database():
    global client, database

    if not MONGODB_URI:
        raise RuntimeError(
            "MONGODB_URI is missing. Add it to backend/.env"
        )

    client = AsyncIOMotorClient(MONGODB_URI)

    try:
        await client.admin.command("ping")
        database = client["voxhire_ai"]
        print("MongoDB connected successfully!")
    except Exception:
        client.close()
        client = None
        database = None
        raise


def get_database():
    if database is None:
        raise RuntimeError("MongoDB is not connected.")

    return database


async def close_database():
    global client, database

    if client:
        client.close()

    client = None
    database = None
