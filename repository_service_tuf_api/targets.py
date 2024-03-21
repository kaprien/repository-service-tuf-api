# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
)


class ResponseData(BaseModel):
    targets: List[str]
    task_id: str
    last_update: datetime


class Response(BaseModel):
    """
    Targets Response
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "targets": ["file1.tar.gz", "file2.tar.gz"],
                    "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "New Artifact(s) successfully submitted.",
            }
        }
    )

    data: ResponseData | None = None
    message: str | None = None


class TargetsInfo(BaseModel):
    length: int
    hashes: Dict[str, str] = Field(
        description=(
            "The key(s) must be compatible with the algorithm(s) supported by "
            "a TUF client"
        )
    )
    custom: Dict[str, Any] | None = None


class Targets(BaseModel):
    info: TargetsInfo
    path: str


with open("tests/data_examples/targets/payload.json") as f:
    content = f.read()
add_payload = json.loads(content)


class AddPayload(BaseModel):
    """
    POST method required Payload.
    """

    model_config = ConfigDict(json_schema_extra={"example": add_payload})
    targets: List[Targets]
    add_task_id_to_custom: bool = Field(
        default=False,
        description="Whether to add the id of the task in custom",
    )
    publish_targets: bool = Field(
        default=True, description="Whether to publish the targets"
    )


class DeletePayload(BaseModel):
    """
    DELETE method required Payload.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "targets": [
                    "v3.4.1/file-3.4.1.tar.gz",
                    "config-3.4.1.yaml",
                    "file1.tar.gz",
                ]
            }
        }
    )
    targets: List[str]
    publish_targets: bool = Field(
        default=True, description="Whether to publish the targets changes"
    )


def post(payload: AddPayload) -> Response:
    """
    Post new targets.
    It will send a new task with the validated payload to the
    ``metadata_repository`` broker queue.
    It generates a new task id, syncs with the Redis server, and posts the new
    task.
    """
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"It requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()
    if payload.add_task_id_to_custom is True:
        new_targets: List[Targets] = []
        for target in payload.targets:
            if target.info.custom:
                target.info.custom = {
                    "added_by_task_id": task_id,
                    **target.info.custom,
                }
            else:
                target.info.custom = {"added_by_task_id": task_id}

            new_targets.append(target)

        payload.targets = new_targets

    repository_metadata.apply_async(
        kwargs={
            "action": "add_targets",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "New Artifact(s) successfully submitted."
    if payload.publish_targets is False:
        message += " Publishing will be skipped."

    data = {
        "targets": [target.path for target in payload.targets],
        "task_id": task_id,
        "last_update": datetime.now(),
    }
    return Response(data=data, message=message)


def delete(payload: DeletePayload) -> Response:
    """
    Delete new targets.
    It will send a new task with the validated payload to the
    ``metadata_repository`` broker queue.
    It generates a new task id, syncs with the Redis server, and posts the new
    task.
    """
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"It requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "remove_targets",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    data = {
        "targets": payload.targets,
        "task_id": task_id,
        "last_update": datetime.now(),
    }

    message = "Remove Artifact(s) successfully submitted."
    if payload.publish_targets is False:
        message += " Publishing will be skipped."
    return Response(data=data, message=message)


def post_publish_targets() -> Response:
    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "publish_targets",
            "payload": None,
        },
        task_id=task_id,
        queue="rstuf_internals",
        acks_late=True,
    )

    data = {
        "targets": [],
        "task_id": task_id,
        "last_update": datetime.now(),
    }

    return Response(
        data=data, message="Publish targets successfully submitted."
    )
