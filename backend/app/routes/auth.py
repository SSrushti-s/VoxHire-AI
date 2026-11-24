
from datetime import datetime, timezone
import re
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_database
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)


router = APIRouter()


# -----------------------------
# Request models
# -----------------------------

class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters.")

        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        value = value.strip().lower()

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Please enter a valid email address.")

        return value


class LoginRequest(BaseModel):
    email: str
    password: str


# -----------------------------
# Response helper
# -----------------------------

def public_user(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }


# -----------------------------
# Signup
# -----------------------------

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):

    db = get_database()

    user_document = {
        "name": request.name,
        "email": request.email,
        "hashed_password": hash_password(request.password),
        "created_at": datetime.now(timezone.utc)
    }

    try:
        # Email must be unique.
        await db.users.create_index("email", unique=True)

        result = await db.users.insert_one(user_document)

        user_document["_id"] = result.inserted_id

        token = create_access_token(str(result.inserted_id))

        return {
            "message": "Account created successfully.",
            "access_token": token,
            "token_type": "bearer",
            "user": public_user(user_document)
        }

    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )


# -----------------------------
# Login
# -----------------------------

@router.post("/login")
async def login(request: LoginRequest):

    db = get_database()

    email = request.email.strip().lower()

    user = await db.users.find_one({
        "email": email
    })

    if not user or not verify_password(
        request.password,
        user["hashed_password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(str(user["_id"]))

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": public_user(user)
    }


# -----------------------------
# Current logged-in user
# -----------------------------

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):

    return {
        "user": public_user(current_user)
    }
