import os
import logging
import hashlib
import base64
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from app.models.user import TokenData

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY         = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM          = "HS256"
TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 scheme — expects: Authorization: Bearer <token> ───────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password helpers ──────────────────────────────────────────────────────────
def _prehash(password: str) -> str:
    """
    Pre-hash password with SHA-256 + base64 before bcrypt.
    Solves bcrypt 72-byte limit — works for passwords of any length.
    """
    return base64.b64encode(
        hashlib.sha256(password.encode("utf-8")).digest()
    ).decode("utf-8")


def hash_password(password: str) -> str:
    prehashed = (_prehash(password))
    print(f"Prehashed length: {len(prehashed)}")
    return pwd_context.hash(prehashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_prehash(plain_password), hashed_password)


# ── Token helpers ─────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> tuple[str, int]:
    """Creates a JWT token. Returns (token, expires_in_seconds)."""
    if not SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")

    expires_in_seconds = TOKEN_EXPIRE_HOURS * 3600
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

    payload = data.copy()
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Token created for user: {data.get('sub')} | expires in {TOKEN_EXPIRE_HOURS}h")
    return token, expires_in_seconds


def decode_token(token: str) -> TokenData:
    """Decodes and validates a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return TokenData(username=username)
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception


# ── FastAPI dependency — use this to protect routes ───────────────────────────
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    return decode_token(token)