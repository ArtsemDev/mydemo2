from demo.handlers import router
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from demo.dependencies import check_session
from demo.models import User
from demo.schemas import UserRegisterForm, UserLoginForm
from demo.utils import create_password_hash, verify_password, create_jwt
from src.dependencies import DBSession
from pages.router import router as router_pages
from src.config import static

app = FastAPI()
app.include_router(router=router)
# app.include_router(router=router, dependencies=[check_session])
app.include_router(router=router_pages)
app.mount(path="/static", app=static, name="static")

app.add_middleware(
    middleware_class=SessionMiddleware,
    secret_key="w8yuehfoqiebvoewpjvewvr",
    session_cookie="sessionID",
)
app.add_middleware(middleware_class=ProxyHeadersMiddleware, trusted_hosts=("*",))


@app.post(path="/signup", name="signup", status_code=status.HTTP_201_CREATED)
async def signup(session: DBSession, form: UserRegisterForm):
    password_hash = create_password_hash(password=form.password)
    user = User(
        **form.model_dump(exclude={"confirm_password"}) | {"password": password_hash}
    )
    session.add(instance=user)
    try:
        await session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"user with email {form.email} exist",
        )
    return "OK"


@app.post(
    path="/signin",
    name="signin",
    status_code=status.HTTP_200_OK,
    response_class=PlainTextResponse,
)
async def signin(session: DBSession, form: UserLoginForm):
    user = await session.scalar(statement=select(User).filter(User.email == form.email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )

    if not verify_password(hashed_password=user.password, plain_password=form.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect password"
        )

    jwt = create_jwt(payload={"sub": user.id})

    return jwt


if __name__ == "__main__":
    from uvicorn import run

    run(app=app, host="0.0.0.0", port=80)
