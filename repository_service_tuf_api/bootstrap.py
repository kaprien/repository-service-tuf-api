# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
import logging
import time
from threading import Thread
from typing import Dict, Literal, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from repository_service_tuf_api import (
    get_task_id,
    is_bootstrap_done,
    pre_lock_bootstrap,
    release_bootstrap_lock,
    repository_metadata,
)
from repository_service_tuf_api.common_models import (
    BaseErrorResponse,
    Roles,
    TUFMetadata,
)


class ServiceSettings(BaseModel):
    targets_base_url: str
    number_of_delegated_bins: int = Field(gt=1, lt=16385)
    targets_online_key: bool


class Settings(BaseModel):
    expiration: Dict[Roles.values(), int]
    services: ServiceSettings


class BootstrapPayload(BaseModel):
    settings: Settings
    metadata: Dict[Literal[Roles.ROOT.value], TUFMetadata]
    timeout: Optional[int] = 300

    class Config:
        with open("tests/data_examples/bootstrap/payload.json") as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {"example": example}


class PostData(BaseModel):
    task_id: Optional[str]


class BootstrapPostResponse(BaseModel):
    data: Optional[PostData]
    message: str

    class Config:
        example = {
            "data": {
                "task_id": "7a634b556f784ae88785d36425f9a218",
            },
            "message": "Bootstrap accepted.",
        }

        schema_extra = {"example": example}


class GetData(BaseModel):
    bootstrap: bool
    state: Optional[str]


class BootstrapGetResponse(BaseModel):
    data: Optional[GetData]
    message: str

    class Config:
        example = {
            "data": {"bootstrap": False},
            "message": "System available for bootstrap.",
        }

        schema_extra = {"example": example}


def _check_bootstrap_status(task_id, timeout):
    time_timeout = time.time() + timeout

    while True:
        task = repository_metadata.AsyncResult(task_id)
        if task.status == "SUCCESS":
            return
        elif task.status == "FAILURE":
            release_bootstrap_lock()
            return
        else:
            if time.time() > time_timeout:
                task.revoke(terminate=True)
                release_bootstrap_lock()
                return

            continue


def get_bootstrap():
    bootstrap = is_bootstrap_done()

    if bootstrap is None:
        response = BootstrapGetResponse(
            data={"bootstrap": False},
            message="System available for bootstrap.",
        )
    elif "pre" in bootstrap:
        response = BootstrapGetResponse(
            data={"bootstrap": True, "state": bootstrap.split("-")[0]},
            message="System LOCKED for bootstrap.",
        )
    else:
        response = BootstrapGetResponse(
            data={"bootstrap": True, "state": "finished"},
            message="System LOCKED for bootstrap.",
        )

    return response


def post_bootstrap(payload: BootstrapPayload) -> BootstrapPostResponse:
    if is_bootstrap_done() is not None:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=BaseErrorResponse(
                error="System already has a Metadata."
            ).dict(exclude_none=True),
        )

    task_id = get_task_id()
    pre_lock_bootstrap(task_id)
    repository_metadata.apply_async(
        kwargs={
            "action": "bootstrap",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    logging.info(f"Bootstrap task {task_id} sent")

    # start a thread to check the bootstrap process
    logging.info(f"Bootstrap process timeout: {payload.timeout} seconds")
    Thread(
        None,
        _check_bootstrap_status,
        kwargs={
            "task_id": task_id,
            "timeout": payload.timeout,
        },
    ).start()

    return BootstrapPostResponse(
        data={"task_id": task_id}, message="Bootstrap accepted."
    )
