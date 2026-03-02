import logging
from app.services.database import db
from app.core.auth import hash_password, verify_password
from app.models.user import UserInDB

logger = logging.getLogger(__name__)

USERS_COLLECTION = db.database["users"]


async def get_user(username: str) -> UserInDB | None:
    logger.info(f"Getting user {username}")
    doc = await USERS_COLLECTION.find_one({"username": username})
    if doc:
        return UserInDB(**doc)
    return None


async def create_user(username: str, password: str) -> UserInDB:
    logger.info("Creating user")
    existing = await get_user(username)
    if existing:
        raise ValueError(f"User '{username}' already exists.")

    user = UserInDB(
        username=username,
        hashed_password=hash_password(password),
        is_active=True
    )
    await USERS_COLLECTION.insert_one(user.model_dump())
    logger.info(f"User created: {username}")
    return user


async def authenticate_user(username: str, password: str) -> UserInDB | None:
    user = await get_user(username)
    if not user:
        logger.warning(f"Login failed — user not found: {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Login failed — wrong password for: {username}")
        return None
    return user