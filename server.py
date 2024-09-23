import json

import bcrypt
from aiohttp import web
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Session, Announcement, User, engine, init_orm
from schema import CreateAnnouncement, UpdateAnnouncement, CreateUser, UpdateUser


def hash_password(password: str) -> str:
    password = password.encode()
    password = bcrypt.hashpw(password, bcrypt.gensalt())
    return password.decode()


def check_password(password: str, hashed_password: str) -> bool:
    password = password.encode()
    hashed_password = hashed_password.encode()
    return bcrypt.checkpw(password, hashed_password)


app = web.Application()


async def orm_context(app):
    print("START")
    await init_orm()
    yield
    await engine.dispose()
    print("FINISH")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response


app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


def get_http_error(error_cls, msg: str | dict | list):
    return error_cls(
        text=json.dumps(
            {"error": msg},
        ),
        content_type="application/json",
    )


def validate_json(json_data: dict,
                  schema_cls: type[CreateAnnouncement] | type[UpdateAnnouncement] | type[CreateUser] | type[
                      UpdateUser]):
    try:
        return schema_cls(**json_data).dict(exclude_unset=True)
    except ValidationError as err:
        errors = err.errors()
        for error in errors:
            error.pop("ctx", None)
        raise get_http_error(web.HTTPError, errors)


async def add_announcement(announcement: Announcement, session: AsyncSession) -> Announcement:
    session.add(announcement)
    try:
        await session.commit()
    except IntegrityError:
        raise get_http_error(web.HTTPConflict, "anything went wrong")
    return announcement


async def get_announcement_by_id(announcement_id: int, session: AsyncSession) -> Announcement:
    announcement = await session.get(Announcement, announcement_id)
    if announcement is None:
        raise get_http_error(web.HTTPNotFound, "announcement not found")
    return announcement


class AnnouncementView(web.View):

    @property
    def announcement_id(self):
        return int(self.request.match_info["announcement_id"])

    @property
    def session(self) -> AsyncSession:
        return self.request.session

    async def get(self):
        announcement = await get_announcement_by_id(self.announcement_id, self.session)
        return web.json_response(announcement.json)

    async def post(self):
        announcement_data = await self.request.json()
        json_data = validate_json(announcement_data, CreateAnnouncement)
        announcement = Announcement(**json_data)
        announcement = add_announcement(announcement, self.session)
        return web.json_response({"id": announcement.id})

    async def patch(self, announcement_id):
        announcement_data = await self.request.json()
        json_data = validate_json(announcement_data, UpdateAnnouncement)
        announcement = await get_announcement_by_id(announcement_id)
        for field, value in json_data.items():
            setattr(announcement, field, value)
        announcement = add_announcement(announcement, self.session)
        return web.json_response({"id": announcement.id})

    async def delete(self, announcement_id):
        announcement = await get_announcement_by_id(announcement_id, self.session)
        await self.session.delete(announcement)
        await self.session.commit()
        return web.json_response({"status": "deleted"})


async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise get_http_error(web.HTTPNotFound, "user not found")
    return user


async def add_user(user: User, session: AsyncSession) -> User:
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise get_http_error(web.HTTPConflict, "user already exists")
    return user


class UserView(web.View):

    @property
    def user_id(self):
        return int(self.request.match_info["user_id"])

    @property
    def session(self) -> AsyncSession:
        return self.request.session

    async def get(self):
        user = await get_user_by_id(self.user_id, self.session)
        return web.json_response(user.dict)

    async def post(self):
        user_data = await self.request.json()
        json_data = validate_json(user_data, CreateUser)
        json_data["password"] = hash_password(json_data["password"])
        user = User(**json_data)
        user = await add_user(user, self.session)
        return web.json_response({"id": user.id})

    async def patch(self):
        user_data = await self.request.json()
        json_data = validate_json(user_data, UpdateUser)
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        user = await get_user_by_id(self.user_id, self.session)
        for field, value in json_data.items():
            setattr(user, field, value)
        user = await add_user(user, self.session)
        return web.json_response({"id": user.id})

    async def delete(self):
        user = await get_user_by_id(self.user_id, self.session)
        await self.session.delete(user)
        await self.session.commit()
        return web.json_response({"status": "deleted"})


app.add_routes(
    [
        web.post("/user/", UserView),
        web.get("/user/{user_id:\d+}/", UserView),
        web.patch("/user/{user_id:\d+}/", UserView),
        web.delete("/user/{user_id:\d+}/", UserView),
        web.post("/announcement/", AnnouncementView),
        web.get("/announcement/{announcement_id:\d+}/", AnnouncementView),
        web.patch("/announcement/{announcement_id:\d+}/", AnnouncementView),
        web.delete("/announcement/{announcement_id:\d+}/", AnnouncementView),
    ]
)

web.run_app(app)
