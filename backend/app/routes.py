from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.catalog import IMAGES, INSTANCE_TYPES
from app.models import (
    CreateInstanceRequest,
    DnsRecord,
    ErrorResponse,
    Image,
    Instance,
    InstanceType,
)
from app.service import InstanceService


def get_instance_service(request: Request) -> InstanceService:
    return request.app.state.instance_service


InstanceServiceDep = Annotated[InstanceService, Depends(get_instance_service)]

router = APIRouter(prefix="/api")


@router.get("/instance-types")
async def list_instance_types() -> list[InstanceType]:
    return INSTANCE_TYPES


@router.get("/images")
async def list_images() -> list[Image]:
    return IMAGES


@router.get("/instances")
async def list_instances(service: InstanceServiceDep) -> list[Instance]:
    return service.list_instances()


@router.post(
    "/instances",
    status_code=202,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_instance(
    body: CreateInstanceRequest, service: InstanceServiceDep, response: Response
) -> Instance:
    instance = service.create_instance(body)
    response.headers["Location"] = f"/api/instances/{instance.id}"
    return instance


@router.get("/instances/{instance_id}", responses={404: {"model": ErrorResponse}})
async def get_instance(instance_id: str, service: InstanceServiceDep) -> Instance:
    return service.get_instance(instance_id)


@router.delete(
    "/instances/{instance_id}",
    status_code=202,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def delete_instance(instance_id: str, service: InstanceServiceDep) -> Instance:
    return service.delete_instance(instance_id)


@router.get("/dns/records")
async def list_dns_records(service: InstanceServiceDep) -> list[DnsRecord]:
    return service.dns_records()
