from datetime import datetime, timedelta

from fastapi import HTTPException
from jwt import encode, decode
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from starlette import status

from demo.config import pwd_context, config


def create_password_hash(password: str) -> str:
    return pwd_context.hash(secret=password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    return pwd_context.verify(secret=plain_password, hash=hashed_password)


def create_jwt(*, payload: dict, exp: int, key: str, algorithm: str) -> str:
    # payload["exp"] = datetime.now() + timedelta(minutes=config.JWT_EXP)
    payload.update({"exp": datetime.now() + timedelta(minutes=config.JWT_EXP)})
    return encode(payload=payload, key=key, algorithm=algorithm)


def create_access_token(payload: dict) -> str:
    return create_jwt(
        payload=payload,
        exp=config.JWT_EXP,
        algorithm="HS256",
        key=config.JWT_SECRET_KEY
    )


def verify_jwt(jwt: str) -> dict:
    try:
        payload = decode(jwt=jwt, key=config.JWT_SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        return payload
