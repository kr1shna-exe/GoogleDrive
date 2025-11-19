import jwt
from fastapi import HTTPException, Request

from exports.prisma import db
from routes.auth import JWT_SECRET


async def authenticateUser(req: Request):
    token = req.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication Revoked")
    try:
        payload = jwt.decode(token, JWT_SECRET)
        user_id = payload.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid Token")
        user = db.user.find_unique(where={"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        print("Unknown Error Occured:", str(e))
