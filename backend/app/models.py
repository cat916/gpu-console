import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic_core import PydanticCustomError

DNS_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


def ensure_dns_label(name: str) -> str:
    if not DNS_LABEL.fullmatch(name):
        raise PydanticCustomError(
            "dns_label",
            "Use lowercase letters, digits and hyphens, starting and ending with a letter or digit",
        )
    return name


InstanceName = Annotated[str, Field(min_length=1, max_length=63), AfterValidator(ensure_dns_label)]


class InstanceStatus(StrEnum):
    PROVISIONING = "provisioning"
    RUNNING = "running"
    ERROR = "error"
    DELETING = "deleting"


class InstanceType(BaseModel):
    id: str
    gpu_model: str
    gpu_count: int
    vcpus: int
    memory_gb: int
    price_per_hour: float


class Image(BaseModel):
    id: str
    name: str


class CreateInstanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: InstanceName
    instance_type: str
    image: str


class Instance(BaseModel):
    id: str
    name: str
    hostname: str
    instance_type: str
    image: str
    status: InstanceStatus
    ip: str | None
    created_at: datetime
    updated_at: datetime


class DnsRecord(BaseModel):
    name: str
    type: Literal["A"] = "A"
    value: str
    ttl: int


class FieldError(BaseModel):
    field: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: list[FieldError] = []


class ErrorResponse(BaseModel):
    error: ErrorDetail
