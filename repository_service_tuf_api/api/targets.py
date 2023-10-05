# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import APIRouter, Security, requests, status

from repository_service_tuf_api import SCOPES_NAMES, targets
from repository_service_tuf_api.api import get_auth

deprecation_warning = (
    " Deprecation Warning: this endpoint will removed in v1.0.0, "
    "use `/api/v1/artifacts`"
)

auth = get_auth()

router = APIRouter(
    prefix="/artifacts",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary=(
        "Add artifacts to Metadata. "
        f"Scope: {SCOPES_NAMES.write_targets.value}"
    ),
    description="Add artifacts to Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: targets.AddPayload,
    request: requests.Request,
    _user=Security(auth, scopes=[SCOPES_NAMES.write_targets.value]),
):
    response = targets.post(payload)

    return response


@router.delete(
    "/",
    summary=(
        "Remove artifacts from Metadata. "
        f"Scope: {SCOPES_NAMES.delete_targets.value}"
    ),
    description="Remove artifacts from Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def delete(
    payload: targets.DeletePayload,
    request: requests.Request,
    _user=Security(auth, scopes=[SCOPES_NAMES.delete_targets.value]),
):
    response = targets.delete(payload)

    return response


@router.post(
    "/publish/",
    summary=(
        "Submit a task to publish artifacts."
        f"Scope: {SCOPES_NAMES.write_targets.value}"
    ),
    description=(
        "Trigger a task to publish artifacts not yet published from the "
        "RSTUF Database"
    ),
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_publish_targets(
    request: requests.Request,
    _user=Security(auth, scopes=[SCOPES_NAMES.write_targets.value]),
):
    response = targets.post_publish_targets()

    return response
