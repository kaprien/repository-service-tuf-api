# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, status

from repository_service_tuf_api import metadata

router = APIRouter(
    prefix="/metadata",
    tags=["Metadata"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary="Post a task to rotate role metadata.",
    description=(
        "Submit an asynchronous task to rotate "
        "a role metadata that requires offline signing. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=metadata.MetadataPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(payload: metadata.MetadataPostPayload):
    return metadata.post_metadata(payload)


@router.get(
    "/sign",
    summary=(
        "Get all metadata roles pending signatures together with their latest "
        "trusted versions."
    ),
    description=(
        "Get all metadata roles that need more signatures before they can be "
        "used and their corresponding latest trusted versions."
    ),
    response_model=metadata.MetadataSignGetResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def get_sign():
    return metadata.get_metadata_sign()


@router.post(
    "/sign",
    summary="Post a task to add a signature for a metadata role.",
    description=(
        "Submit an asynchronous task to add a signature "
        "for a metadata role. "
        "Use the task ID to retrieve the task status in the endpoint "
        "/api/v1/task."
    ),
    response_model=metadata.MetadataPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_sign(payload: metadata.MetadataSignPostPayload):
    return metadata.post_metadata_sign(payload)


@router.post(
    "/sign/delete",
    summary="Post a task to delete role metadata in signing process.",
    description=(
        "Submit an asynchronous task to delete role metadata in "
        "signing process. "
        "Check the status and result using the task ID and the "
        "`get task state` endpoint."
    ),
    response_model=metadata.MetadataSignDeleteResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_delete_sign(payload: metadata.MetadataSignDeletePayload):
    return metadata.delete_metadata_sign(payload)
