import flask
from flask import jsonify, request
from flask.views import MethodView
from flask_bcrypt import Bcrypt
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from models import Session, Announcement, User
from schema import CreateAnnouncement, UpdateAnnouncement, CreateUser, UpdateUser

app = flask.Flask("app")
bcrypt = Bcrypt(app)


class HttpError(Exception):

    def __init__(self, status_code: int, error_msg: str | dict | list):
        self.status_code = status_code
        self.error_msg = error_msg


@app.errorhandler(HttpError)
def http_error_handler(err: HttpError):
    http_response = jsonify({"status": "error", "message": err.error_msg})
    http_response.status = err.status_code
    return http_response


def validate_json(json_data: dict,
                  schema_cls: type[CreateAnnouncement] | type[UpdateAnnouncement] | type[CreateUser] | type[
                      UpdateUser]):
    try:
        return schema_cls(**json_data).dict(exclude_unset=True)
    except ValidationError as err:
        errors = err.errors()
        for error in errors:
            error.pop("ctx", None)
        raise HttpError(400, errors)


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_request(http_response: flask.Response):
    request.session.close()
    return http_response


def add_announcement(announcement: Announcement):
    request.session.add(announcement)
    request.session.commit()

    return announcement


def get_announcement(announcement_id: int):
    announcement = request.session.get(Announcement, announcement_id)
    if announcement is None:
        raise HttpError(404, "announcement not found")
    return announcement


class AnnouncementView(MethodView):

    def get(self, announcement_id: int):
        announcement = get_announcement(announcement_id)
        return jsonify(announcement.json)

    def post(self):
        json_data = validate_json(request.json, CreateAnnouncement)
        announcement = Announcement(**json_data)
        announcement = add_announcement(announcement)
        return jsonify({"id": announcement.id})

    def patch(self, announcement_id):
        json_data = validate_json(request.json, UpdateAnnouncement)
        announcement = get_announcement(announcement_id)
        for field, value in json_data.items():
            setattr(announcement, field, value)
        announcement = add_announcement(announcement)
        return announcement.json

    def delete(self, announcement_id):
        announcement = get_announcement(announcement_id)
        request.session.delete(announcement)
        request.session.commit()
        return jsonify({"status": "deleted"})


def add_user(user: User):
    try:
        request.session.add(user)
        request.session.commit()
    except IntegrityError:
        raise HttpError(409, "user already exists")
    return user


def get_user(user_id: int):
    user = request.session.get(User, user_id)
    if user is None:
        raise HttpError(404, "user not found")
    return user


def hash_password(password: str):
    password = password.encode()
    password = bcrypt.generate_password_hash(password)
    password = password.decode()
    return password


def check_password(password: str, hashed_password: str):
    password = password.encode()
    hashed_password = hashed_password.encode()
    return bcrypt.check_password_hash(hashed_password, password)


class UserView(MethodView):

    def get(self, user_id: int):
        user = get_user(user_id)
        return jsonify(user.json)

    def post(self):
        json_data = validate_json(request.json, CreateUser)
        json_data["password"] = hash_password(json_data["password"])
        user = User(**json_data)
        user = add_user(user)
        return jsonify({"id": user.id})

    def patch(self, user_id):
        json_data = validate_json(request.json, UpdateUser)
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        user = get_user(user_id)
        for field, value in json_data.items():
            setattr(user, field, value)
        user = add_user(user)
        return user.json

    def delete(self, user_id):
        user = get_user(user_id)
        request.session.delete(user)
        request.session.commit()
        return jsonify({"status": "deleted"})


announcement_view = AnnouncementView.as_view("announcement")
user_view = UserView.as_view("user")

app.add_url_rule("/announcement/", view_func=announcement_view, methods=["POST"])
app.add_url_rule(
    "/announcement/<int:announcement_id>/", view_func=announcement_view, methods=["GET", "PATCH", "DELETE"]
)

app.add_url_rule("/user/", view_func=user_view, methods=["POST"])
app.add_url_rule(
    "/user/<int:user_id>/", view_func=user_view, methods=["GET", "PATCH", "DELETE"]
)

app.run()
