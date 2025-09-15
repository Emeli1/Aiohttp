import datetime
import jwt
from aiohttp import web
from sqlalchemy import select

from models import init_orm, close_orm, AsyncSession, User, Advertisement
import json
from sqlalchemy.exc import IntegrityError
from schema import RegisterRequest, AuthRequest, validate
from auth import hash_password, check_password

SECRET_KEY = '1234'

def create_token(user_id):
    playload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    }
    token = jwt.encode(playload, SECRET_KEY, algorithm="HS256")
    return token


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:  # токен истёк
        return None
    except jwt.InvalidTokenError:  # неверный токен
        return None


async def orm_context(app: web.Application):
    print("START")
    await init_orm()
    yield
    await close_orm()
    print("FINISH")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with AsyncSession() as session:
        request["session"] = session
        result = await handler(request)
        return result


def create_error(error_cls, error_message: str | dict | list):
    error = json.dumps({"error": error_message})
    return error_cls(
        text=error,
        content_type="application/json"
    )


@web.middleware
async def auth_middlewear(request: web.Request, handler):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
            user_id = decode_token(token)
            request["user_id"] = user_id  # Сохраняем user_id в request
        except IndexError:
            pass  # Недопустимый формат заголовка
    else:
        request["user_id"] = None

    response = await handler(request)
    return response


async def register(request: web.Request):
    session: AsyncSession = request.get('session')
    json_data = await request.json()
    json_data = validate(RegisterRequest, json_data)
    hashed_password = hash_password(json_data["password"])
    user = User(
        name=json_data["name"],
        password=hashed_password
    )
    try:
        session.add(user)
        await session.commit()
        return web.Response(text="User registered successfully.", status=201)
    except IntegrityError:
        await session.rollback()
        raise create_error(web.HTTPConflict, "User with this name already exists.")


async def login(request: web.Request):
    session: AsyncSession = request.get('session')
    json_data = await request.json()
    try:
        json_data = validate(AuthRequest, json_data)
    except Exception as e:
        print(e)
        raise create_error(web.HTTPBadRequest, "Invalid data")

    query = select(User).filter_by(name=json_data["name"])
    result = await session.execute(query)
    user = result.scalars().first()  # Получаем первого пользователя (если есть)
    if user and check_password(json_data["password"], user.password):
        token = create_token(user.id)
        return web.json_response({"status": "Login successful", "token": token}, status=201)
    else:
        raise create_error(web.HTTPUnauthorized, "Invalid name or password.")


async def get_adv_by_id(session: AsyncSession, advertisement_id: int):
    adv = await session.get(Advertisement, advertisement_id)
    if adv is None:
        raise create_error(web.HTTPNotFound, "Advertisement not found")
    return adv


async def add_adv(session: AsyncSession, adv: Advertisement):
    try:
        session.add(adv)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise create_error(web.HTTPConflict, "Advertisement already exists")


app = web.Application()
app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)
app.middlewares.append(auth_middlewear)


class AdvertisementView(web.View):
    def __init__(self, request: web.Request, session: AsyncSession):
        self._request = request  # Используем _request для хранения объекта request
        self._session = session
        self.advs_id = int(self.request.match_info["advertisement_id"]) \
            if "advertisement_id" in self.request.match_info \
            else None # adv_id в конструктор


    @property
    def session(self) -> AsyncSession:
        return self._session

    @property
    def adv_id(self) -> int:
        return int(self.request.match_info["advertisement_id"])

    async def auth(self):
        user_id = self.request.get("user_id")
        if not user_id:
            raise create_error(web.HTTPUnauthorized, "Unauthorized")
        return True

    async def get_adv(self) -> Advertisement:
        return await get_adv_by_id(self.session, self.adv_id)

    async def get(self):
        adv = await self.get_adv()
        return web.json_response(adv.json)

    async def post(self):
        await self.auth()
        json_data = await self.request.json()
        adv = Advertisement(
            name=json_data["name"],
            description=json_data["description"],
            owner_id=json_data["owner_id"]
        )
        await add_adv(self.session, adv)
        return web.json_response(adv.id_dict)

    async def patch(self):
        await self.auth()
        adv = await self.get_adv()
        json_data = await self.request.json()
        if "name" in json_data:
            adv.name = json_data["name"]
        if "description" in json_data:
            adv.description = json_data["description"]
        await add_adv(self.session, adv)
        return web.json_response(adv.json)

    async def delete(self):
        await self.auth()
        adv = await self.get_adv()
        await self.session.delete(adv)
        return web.json_response({"status": "deleted"})


async def adv_factory(request): # фабрика view, которая будет создавать экземпляры AdvertisementView с передачей сессии
    view = AdvertisementView(request, request["session"])
    if request.method == "GET":
        return await view.get()
    elif request.method == "POST":
        return await view.post()
    elif request.method == "PATCH":
        return await view.patch()
    elif request.method == "DELETE":
        return await view.delete()
    else:
        raise web.HTTPMethodNotAllowed(method=request.method, allowed_methods=['GET', 'POST', 'PATCH', 'DELETE'])

app.add_routes([
    web.post(r"/register", register),
    web.post(r"/login", login),
    web.post(r"/advs", adv_factory),
    web.get(r"/advs/{advertisement_id:\d+}", adv_factory),
    web.patch(r"/advs/{advertisement_id:\d+}", adv_factory),
    web.delete(r"/advs/{advertisement_id:\d+}", adv_factory),
])


web.run_app(app)