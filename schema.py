from pydantic import BaseModel, field_validator


class AnnouncementBase(BaseModel):
    title: str | None = None
    description: str | None = None
    user_id: int | None = None


class UpdateAnnouncement(AnnouncementBase):
    title: str | None = None
    description: str | None = None
    user_id: int | None = None


class CreateAnnouncement(AnnouncementBase):
    title: str
    description: str
    user_id: int


class UserBase(BaseModel):
    name: str | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if len(value) < 8:
            raise ValueError("password is too short")
        return value


class UpdateUser(UserBase):
    name: str | None = None
    password: str | None = None


class CreateUser(UserBase):
    name: str
    password: str
