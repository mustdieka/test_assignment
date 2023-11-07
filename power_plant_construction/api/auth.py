from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import getLogger

from asyncpg import Pool
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import DecodeError, ExpiredSignatureError
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED
import jwt

from contracts.schemas.user import UserRole
from power_plant_construction.db import get_db_pool
from power_plant_construction.repositories.user import UserRepo, get_user_repo

log = getLogger(__name__)
SECRET_KEY = "5ee4f095b0ae38f39e11c842c9f10e8e4d8c38348197b0561908a5d281ddd85a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 780


class Token(BaseModel):
    access_token: str
    token_type: str


@dataclass
class LoggedInUser:
    user: str
    role: UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth")

router = APIRouter()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


async def get_logged_in_user(
    token: str = Depends(oauth2_scheme),
    pool: Pool = Depends(get_db_pool),
    user_repository: UserRepo = Depends(get_user_repo),
) -> LoggedInUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except DecodeError:
        raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with pool.acquire() as conn:
        user = await user_repository.fetch_by_id(conn, entity_id=user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Something went wrong",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return LoggedInUser(user=user_id, role=user.role)


class Authenticator:
    def __init__(self, whitelisted_roles: frozenset[UserRole] | None) -> None:
        self._whitelisted_roles = whitelisted_roles

    async def __call__(self, logged_in_user: LoggedInUser = Depends(get_logged_in_user)) -> LoggedInUser:
        if self._whitelisted_roles is not None:
            if logged_in_user.role not in self._whitelisted_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Missing required roles",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return logged_in_user


@router.post(
    "",
    response_model=Token,
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    pool: Pool = Depends(get_db_pool),
    user_repo: UserRepo = Depends(get_user_repo),
) -> dict[str, str]:
    async with pool.acquire() as conn:
        user = await user_repo.fetch_by_login(conn, login=form_data.username)
        if not user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password or this method of login is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user or not user.verify_password(form_data.password):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password or this method of login is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.entity_id,
                "role": user.role,
            },
            expires_delta=access_token_expires,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }


MINIMAL_AUTH = Authenticator(whitelisted_roles=frozenset((UserRole.WORKER, UserRole.MANAGER)))
MANAGER_AUTH = Authenticator(whitelisted_roles=frozenset((UserRole.MANAGER,)))

BASIC_SECURITY = HTTPBasic()
