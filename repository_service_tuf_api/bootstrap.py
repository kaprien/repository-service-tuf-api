# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
import logging
import time
from datetime import datetime
from threading import Thread
from typing import Dict, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    pre_lock_bootstrap,
    release_bootstrap_lock,
    repository_metadata,
)
from repository_service_tuf_api.common_models import (
    BaseErrorResponse,
    Roles,
    TUFMetadata,
)

with open("tests/data_examples/bootstrap/payload.json") as f:
    content = f.read()
payload_example = json.loads(content)


class ServiceSettings(BaseModel):
    targets_base_url: str
    number_of_delegated_bins: int = Field(gt=1, lt=16385)
    targets_online_key: bool


class Settings(BaseModel):
    expiration: Dict[Roles.values(), int]
    services: ServiceSettings


class BootstrapPayload(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": payload_example})
    settings: Settings
    metadata: Dict[Literal[Roles.ROOT.value], TUFMetadata]
    timeout: int | None = Field(default=300, description="Timeout in seconds")


class PostData(BaseModel):
    task_id: str | None = None
    last_update: datetime


class BootstrapPostResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Bootstrap accepted.",
            }
        }
    )
    data: PostData | None = None
    message: str


class GetData(BaseModel):
    bootstrap: bool
    state: str | None = None
    id: str | None = None


class BootstrapGetResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {"bootstrap": False},
                "message": "System available for bootstrap.",
            }
        }
    )
    data: GetData | None = None
    message: str


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


def get_bootstrap() -> BootstrapGetResponse:
    bs_state = bootstrap_state()
    # If bootstrap ceremony has completed, is executed in the moment ("pre")
    # or is in the process of DAS signing ("signing") we consider it as locked.
    if bs_state.bootstrap is True or bs_state.state in ["pre", "signing"]:
        message = "System LOCKED for bootstrap."

    else:
        message = "System available for bootstrap."

    response = BootstrapGetResponse(
        data={
            "bootstrap": bs_state.bootstrap,
            "state": bs_state.state,
            "id": bs_state.task_id,
        },
        message=message,
    )

    return response


def post_bootstrap(payload: BootstrapPayload) -> BootstrapPostResponse:
    bs_state = bootstrap_state()
    # If bootstrap ceremony has completed, is executed in the moment ("pre")
    # or is in the process of DAS signing ("signing") we consider it as locked.
    if bs_state.bootstrap is True or bs_state.state in ["pre", "signing"]:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=BaseErrorResponse(
                error=(
                    "System already has a Metadata. "
                    f"State: {bs_state.state}"
                )
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

    data = {
        "task_id": task_id,
        "last_update": datetime.now(),
    }

    return BootstrapPostResponse(
        data=data,
        message="Bootstrap accepted.",
    )
