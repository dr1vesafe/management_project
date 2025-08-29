from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import JWTStrategy

from src.app.auth.user_manager import get_user_manager, UserManager
from src.app.auth.auth import access_backend, refresh_backend

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login')
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager)
):
    credentials = OAuth2PasswordRequestForm(
        username=data.username,
        password=data.password
    )

    user = await user_manager.authenticate(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            datail='Неверный email или пароль'
        )
    
    access_token = await access_backend.get_strategy().write_token(user)

    refresh_token = await refresh_backend.get_strategy().write_token(user)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.post("/refresh")
async def refresh_token(
    token: str,
    user_manager: UserManager = Depends(get_user_manager)
):
    strategy: JWTStrategy = refresh_backend.get_strategy()
    user = await strategy.read_token(token, user_manager)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    new_access_token = await access_backend.get_strategy().write_token(user)
    return {"access_token": new_access_token, "token_type": "bearer"}
    