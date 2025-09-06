from fastapi import APIRouter, Depends, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from src.app.auth.user_manager import get_user_manager, UserManager
from src.app.schemas.user import UserCreate
from src.app.auth.auth import access_backend, refresh_backend

router = APIRouter(prefix='/auth', tags=['auth'])
templates = Jinja2Templates(directory='src/app/templates')


@router.get('/login')
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'error': None})


@router.post('/login')
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    user_manager: UserManager = Depends(get_user_manager)
):
    user = await user_manager.authenticate(OAuth2PasswordRequestForm(
        username=username,
        password=password,
        scope=''
    ))
    if not user:
        return templates.TemplateResponse(
            'login.html', {'request': request, 'error': 'Неверный email или пароль'}
        )
    
    access_token = await access_backend.get_strategy().write_token(user)
    refresh_token = await refresh_backend.get_strategy().write_token(user)

    response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key='access_token', value=f'Bearer {access_token}', httponly=True)
    response.set_cookie(key='refresh_token', value=f'Bearer {refresh_token}', httponly=True)
    return response


@router.get('/refresh')
async def refresh_token(request: Request, user_manager = Depends(get_user_manager)):
    token = request.cookies.get('refresh_token')
    if not token:
        return RedirectResponse(url='/auth/login')

    refresh_token = token.removeprefix('Bearer ').strip()
    user = await refresh_backend.get_strategy().read_token(refresh_token, user_manager)
    if not user:
        return RedirectResponse(url='/auth/login') 

    new_access_token = await access_backend.get_strategy().write_token(user)

    next_url = request.query_params.get('next', '/')
    response = RedirectResponse(url=next_url)
    response.set_cookie('access_token', f'Bearer {new_access_token}', httponly=True)
    return response


@router.get('/logout')
async def logout():
    response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@router.get('/register')
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request, 'error': None})


@router.post('/register')
async def resgister_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    user_manager = Depends(get_user_manager)
):
    if password != password_confirm:
        return templates.TemplateResponse(
            'register.html',
            {'request': request, 'error': 'Пароли не совпадают'}
        )
    
    try:
        await user_manager.create(
            UserCreate(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        )
        return RedirectResponse(url='/auth/login', status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            'register.html',
            {'request': request, 'error': str(e)}
        )
