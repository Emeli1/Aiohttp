from googleapiclient.errors import HttpError
from pydantic import BaseModel, ValidationError, field_validator


class BaseAdvRequest (BaseModel):
    name: str
    description: str
    owner: int


class RegisterRequest(BaseModel):
    name: str
    password: str

    @field_validator("password")
    @classmethod
    def secure_password(clscls, v: str):
        if len(v) < 8:
            raise ValueError("password is too short")
        return v


class AuthRequest(BaseModel):
    name: str
    password: str


class CreateAdvRequest(BaseAdvRequest):
    pass


class UpdateAdvRequest(BaseAdvRequest):
    name: str | None = None
    description: str | None = None
    owner: int | None = None


def validate(
        schema: type[CreateAdvRequest | UpdateAdvRequest], json_data: dict
) -> dict:
    try:
        schema_instance = schema(**json_data)
        return schema_instance.model_dump(exclude_unset=True) # исключает из возвращаемого словаря поля,
    except ValidationError as e:                              # которые не были явно установлены при создании модели.
        errors = e.errors()
        for error in errors:
            error.pop("ctx", None)
        raise HttpError(400, errors)