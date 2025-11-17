import jwt
from fastapi import APIRouter, HTTPException, Response

from exports.prisma import db
from lib.utils import User, compare_password, hash_password

router = APIRouter()
JWT_SECRET = "123"

@router.post("/register")
async def signup(user: User, response: Response):
    email, password = user.email, user.password
    existing_user = await db.user.find_unique(
        where={"email": email}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="You already have an account")
    hashed_password = hash_password(password)
    user = await db.user.create(
        data={
            "email": email,
            "password": hashed_password
        }
    )
    token = jwt.encode({"userId": user.id}, JWT_SECRET)
    response.set_cookie(
        key = "token",
        value = token,
        httponly = True,
        max_age = 10 * 24 * 60 * 60,
        samesite = "strict",
        secure = True
    )
    print("User registered Successfully")
    return {
        "message": "User registered successfully",
        "user": {
            "email": email
        }
    }

@router.post("/login")
async def signin(user: User, response: Response):
    email, password = user.email, user.password
    existing_user = await db.user.find_unique(where={"email": email})
    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")
    pwd_check = compare_password(password, existing_user.password)
    if not pwd_check:
        raise HTTPException(status_code=400, detail="Incorrect Password")
    token = jwt.encode({"userId": existing_user.id}, JWT_SECRET)
    response.set_cookie(
        key = "token",
        value = token,
        httponly = True,
        max_age = 10 * 24 * 60 * 60,
        samesite = "strict",
        secure = True
    )
    print("User loggedin successfully")
    return {
        "message": "User loggedin successfully",
        "user": {
            "email": email
        }
    }
