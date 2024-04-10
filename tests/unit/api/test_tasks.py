# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import pretend
from fastapi import status

TASK_URL = "/api/v1/task/"
MOCK_PATH = "repository_service_tuf_api.tasks"


class TestGetTask:
    def test_get(self, test_client, monkeypatch):
        mocked_task_result = pretend.stub(
            state="SUCCESS",
            result={
                "status": True,
                "task": "add_artifacts",
                "last_update": "2023-11-17T09:54:15.762882",
                "message": "Artifact(s) Added",
                "details": {
                    "added_artifacts": [
                        "file1.tar.gz",
                        "file2.tar.gz",
                        "file3.tar.gz",
                    ],
                    "invalid_paths": [],
                    "target_roles": ["bins-3", "bins-2"],
                },
            },
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )

        test_response = test_client.get(f"{TASK_URL}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "SUCCESS",
                "result": {
                    "task": "add_artifacts",
                    "last_update": "2023-11-17T09:54:15.762882",
                    "message": "Artifact(s) Added",
                    "status": True,
                    "details": {
                        "added_artifacts": [
                            "file1.tar.gz",
                            "file2.tar.gz",
                            "file3.tar.gz",
                        ],
                        "invalid_paths": [],
                        "target_roles": ["bins-3", "bins-2"],
                    },
                },
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]

    def test_get_result_is_exception(self, test_client, monkeypatch):
        mocked_task_result = pretend.stub(
            state="FAILURE", result=ValueError("Failed to load")
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )

        test_response = test_client.get(f"{TASK_URL}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "FAILURE",
                "result": {
                    "message": "Failed to load",
                },
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]

    def test_get_result_is_errored(self, test_client, monkeypatch):
        mocked_task_result = pretend.stub(
            state="SUCCESS",
            result={
                "status": False,
                "task": "sign_metadata",
                "last_update": "2023-11-17T09:54:15.762882",
                "message": "Signature Failed",
                "error": "No signatures pending for root",
            },
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )

        test_response = test_client.get(f"{TASK_URL}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK

        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "ERRORED",
                "result": {
                    "task": "sign_metadata",
                    "last_update": "2023-11-17T09:54:15.762882",
                    "message": "Signature Failed",
                    "status": False,
                    "error": "No signatures pending for root",
                },
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]

    def test_get_result_success_with_empty_result(
        self, test_client, monkeypatch
    ):
        mocked_task_result = pretend.stub(
            state="SUCCESS",
            result={},
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )

        test_response = test_client.get(f"{TASK_URL}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK

        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "ERRORED",
                "result": {},
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]

    def test_get_result_failure_with_empty_result(
        self, test_client, monkeypatch
    ):
        mocked_task_result = pretend.stub(
            state="FAILURE",
            result={},
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )

        test_response = test_client.get(f"{TASK_URL}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK

        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "FAILURE",
                "result": {},
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]
