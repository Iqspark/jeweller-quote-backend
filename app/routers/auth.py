from fastapi import APIRouter, HTTPException, status
import logging

from app.models.user import UserCreate, UserLogin, TokenResponse
from app.services.user_service import create_user, authenticate_user
from app.core.auth import create_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
async def register(user: UserCreate):
    """Create a new user account."""
    logger.info(" **** Creating new user ****")
    try:
        await create_user(username=user.username, password=user.password)
        return {"message": f"User '{user.username}' created successfully."}
    except ValueError as e:
        logger.error(" **** Error creating new user ****")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login with username and password.
    Returns a JWT token valid for JWT_EXPIRE_HOURS hours.
    """
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled.")

    token, expires_in = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in
    )