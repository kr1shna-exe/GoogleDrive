from typing import List

import bcrypt
from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    password: str
    items: List

def compare_password(user_password: str, password: str) -> bool:
    return bcrypt.checkpw(user_password.encode('utf-8'), password.encode('utf-8'))

def hash_password(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
