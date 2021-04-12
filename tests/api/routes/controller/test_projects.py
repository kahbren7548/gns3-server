# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import uuid
import os
import zipfile
import json
import pytest

from fastapi import FastAPI, status
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from tests.utils import asyncio_patch

from gns3server.controller import Controller
from gns3server.controller.project import Project

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def project(app: FastAPI, client: AsyncClient, controller: Controller) -> Project:

    u = str(uuid.uuid4())
    params = {"name": "test", "project_id": u}
    await client.post(app.url_path_for("create_project"), json=params)
    return controller.get_project(u)


async def test_create_project_with_path(app: FastAPI, client: AsyncClient, controller: Controller, tmpdir) -> None:

    params = {"name": "test", "path": str(tmpdir), "project_id": "00010203-0405-0607-0809-0a0b0c0d0e0f"}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "test"
    assert response.json()["project_id"] == "00010203-0405-0607-0809-0a0b0c0d0e0f"
    assert response.json()["status"] == "opened"


async def test_create_project_without_dir(app: FastAPI, client: AsyncClient, controller: Controller) -> None:

    params = {"name": "test", "project_id": "10010203-0405-0607-0809-0a0b0c0d0e0f"}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["project_id"] == "10010203-0405-0607-0809-0a0b0c0d0e0f"
    assert response.json()["name"] == "test"


async def test_create_project_with_uuid(app: FastAPI, client: AsyncClient, controller: Controller) -> None:

    params = {"name": "test", "project_id": "30010203-0405-0607-0809-0a0b0c0d0e0f"}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == 201
    assert response.json()["project_id"] == "30010203-0405-0607-0809-0a0b0c0d0e0f"
    assert response.json()["name"] == "test"


async def test_create_project_with_variables(app: FastAPI, client: AsyncClient, controller: Controller) -> None:

    variables = [
        {"name": "TEST1"},
        {"name": "TEST2", "value": "value1"}
    ]
    params = {"name": "test", "project_id": "30010203-0405-0607-0809-0a0b0c0d0e0f", "variables": variables}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == 201
    assert response.json()["variables"] == [
        {"name": "TEST1"},
        {"name": "TEST2", "value": "value1"}
    ]


async def test_create_project_with_supplier(app: FastAPI, client: AsyncClient, controller: Controller) -> None:

    supplier = {
        'logo': 'logo.png',
        'url': 'http://example.com'
    }
    params = {"name": "test", "project_id": "30010203-0405-0607-0809-0a0b0c0d0e0f", "supplier": supplier}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["supplier"] == supplier


async def test_update_project(app: FastAPI, client: AsyncClient, controller: Controller) -> None:

    params = {"name": "test", "project_id": "10010203-0405-0607-0809-0a0b0c0d0e0f"}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["project_id"] == "10010203-0405-0607-0809-0a0b0c0d0e0f"
    assert response.json()["name"] == "test"

    params = {"name": "test2"}
    response = await client.put(app.url_path_for("update_project", project_id="10010203-0405-0607-0809-0a0b0c0d0e0f"),
                                json=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "test2"


async def test_update_project_with_variables(app: FastAPI, client: AsyncClient, controller: Controller) -> None:

    variables = [
        {"name": "TEST1"},
        {"name": "TEST2", "value": "value1"}
    ]
    params = {"name": "test", "project_id": "10010203-0405-0607-0809-0a0b0c0d0e0f", "variables": variables}
    response = await client.post(app.url_path_for("create_project"), json=params)
    assert response.status_code == status.HTTP_201_CREATED

    params = {"name": "test2"}
    response = await client.put(app.url_path_for("update_project", project_id="10010203-0405-0607-0809-0a0b0c0d0e0f"),
                                json=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["variables"] == variables


async def test_list_projects(app: FastAPI, client: AsyncClient, controller: Controller, tmpdir) -> None:

    params = {"name": "test", "path": str(tmpdir), "project_id": "00010203-0405-0607-0809-0a0b0c0d0e0f"}
    await client.post(app.url_path_for("create_project"), json=params)
    response = await client.get(app.url_path_for("get_projects"))
    assert response.status_code == status.HTTP_200_OK
    projects = response.json()
    assert projects[0]["name"] == "test"


async def test_get_project(app: FastAPI, client: AsyncClient, project: Project) -> None:

    response = await client.get(app.url_path_for("get_project", project_id=project.id))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "test"


async def test_delete_project(app: FastAPI, client: AsyncClient, project: Project, controller: Controller) -> None:

    with asyncio_patch("gns3server.controller.project.Project.delete", return_value=True) as mock:
        response = await client.delete(app.url_path_for("delete_project", project_id=project.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mock.called
        assert project not in controller.projects


async def test_delete_project_invalid_uuid(app: FastAPI, client: AsyncClient) -> None:

    response = await client.delete(app.url_path_for("delete_project", project_id=str(uuid.uuid4())))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_close_project(app: FastAPI, client: AsyncClient, project: Project) -> None:

    with asyncio_patch("gns3server.controller.project.Project.close", return_value=True) as mock:
        response = await client.post(app.url_path_for("close_project", project_id=project.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mock.called


async def test_open_project(app: FastAPI, client: AsyncClient, project: Project) -> None:

    with asyncio_patch("gns3server.controller.project.Project.open", return_value=True) as mock:
        response = await client.post(app.url_path_for("open_project", project_id=project.id))
        assert response.status_code == status.HTTP_201_CREATED
        assert mock.called


async def test_load_project(app: FastAPI, client: AsyncClient, project: Project, config) -> None:

    with asyncio_patch("gns3server.controller.Controller.load_project", return_value=project) as mock:
        response = await client.post(app.url_path_for("load_project"), json={"path": "/tmp/test.gns3"})
        assert response.status_code == status.HTTP_201_CREATED
        mock.assert_called_with("/tmp/test.gns3")
        assert response.json()["project_id"] == project.id


# @pytest.mark.asyncio
# async def test_notification(controller_api, http_client, project, controller):
#
#     async with http_client.get(controller_api.get_url("/projects/{project_id}/notifications".format(project_id=project.id))) as response:
#         response.body = await response.content.read(200)
#         controller.notification.project_emit("node.created", {"a": "b"})
#         response.body += await response.content.readany()
#         assert response.status_code == 200
#         assert b'"action": "ping"' in response.body
#         assert b'"cpu_usage_percent"' in response.body
#         assert b'{"action": "node.created", "event": {"a": "b"}}\n' in response.body
#         assert project.status_code == "opened"
#
#
# @pytest.mark.asyncio
# async def test_notification_invalid_id(controller_api):
#
#     response = await controller_api.get("/projects/{project_id}/notifications".format(project_id=uuid.uuid4()))
#     assert response.status_code == 404


# @pytest.mark.asyncio
# async def test_notification_ws(controller_api, http_client, controller, project):
#
#     ws = await http_client.ws_connect(controller_api.get_url("/projects/{project_id}/notifications/ws".format(project_id=project.id)))
#     answer = await ws.receive()
#     answer = json.loads(answer.data)
#     assert answer["action"] == "ping"
#
#     controller.notification.project_emit("test", {})
#     answer = await ws.receive()
#     answer = json.loads(answer.data)
#     assert answer["action"] == "test"
#
#     if not ws.closed:
#         await ws.close()
#
#     assert project.status_code == "opened"


async def test_export_with_images(app: FastAPI, client: AsyncClient, tmpdir, project: Project) -> None:

    project.dump = MagicMock()
    os.makedirs(project.path, exist_ok=True)
    with open(os.path.join(project.path, 'a'), 'w+') as f:
        f.write('hello')

    os.makedirs(str(tmpdir / "IOS"))
    with open(str(tmpdir / "IOS" / "test.image"), "w+") as f:
        f.write("AAA")

    topology = {
        "topology": {
            "nodes": [
                {
                    "properties": {
                        "image": "test.image"
                    },
                    "node_type": "dynamips"
                }
            ]
        }
    }
    with open(os.path.join(project.path, "test.gns3"), 'w+') as f:
        json.dump(topology, f)

    with patch("gns3server.compute.Dynamips.get_images_directory", return_value=str(tmpdir / "IOS")):
        response = await client.get(app.url_path_for("export_project", project_id=project.id),
                                    params={"include_images": "yes"})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers['CONTENT-TYPE'] == 'application/gns3project'
    assert response.headers['CONTENT-DISPOSITION'] == 'attachment; filename="{}.gns3project"'.format(project.name)

    with open(str(tmpdir / 'project.zip'), 'wb+') as f:
        f.write(response.content)

    with zipfile.ZipFile(str(tmpdir / 'project.zip')) as myzip:
        with myzip.open("a") as myfile:
            content = myfile.read()
            assert content == b"hello"
        myzip.getinfo("images/IOS/test.image")


async def test_export_without_images(app: FastAPI, client: AsyncClient, tmpdir, project: Project) -> None:

    project.dump = MagicMock()
    os.makedirs(project.path, exist_ok=True)
    with open(os.path.join(project.path, 'a'), 'w+') as f:
        f.write('hello')

    os.makedirs(str(tmpdir / "IOS"))
    with open(str(tmpdir / "IOS" / "test.image"), "w+") as f:
        f.write("AAA")

    topology = {
        "topology": {
            "nodes": [
                {
                    "properties": {
                        "image": "test.image"
                    },
                    "node_type": "dynamips"
                }
            ]
        }
    }
    with open(os.path.join(project.path, "test.gns3"), 'w+') as f:
        json.dump(topology, f)

    with patch("gns3server.compute.Dynamips.get_images_directory", return_value=str(tmpdir / "IOS"),):
        response = await client.get(app.url_path_for("export_project", project_id=project.id),
                                    params={"include_images": "0"})
    assert response.status_code == status.HTTP_200_OK
    assert response.headers['CONTENT-TYPE'] == 'application/gns3project'
    assert response.headers['CONTENT-DISPOSITION'] == 'attachment; filename="{}.gns3project"'.format(project.name)

    with open(str(tmpdir / 'project.zip'), 'wb+') as f:
        f.write(response.content)

    with zipfile.ZipFile(str(tmpdir / 'project.zip')) as myzip:
        with myzip.open("a") as myfile:
            content = myfile.read()
            assert content == b"hello"
        # Image should not exported
        with pytest.raises(KeyError):
            myzip.getinfo("images/IOS/test.image")


async def test_get_file(app: FastAPI, client: AsyncClient, project: Project) -> None:

    os.makedirs(project.path, exist_ok=True)
    with open(os.path.join(project.path, 'hello'), 'w+') as f:
        f.write('world')

    response = await client.get(app.url_path_for("get_file", project_id=project.id, file_path="hello"))
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"world"

    response = await client.get(app.url_path_for("get_file", project_id=project.id, file_path="false"))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await client.get(app.url_path_for("get_file", project_id=project.id, file_path="../hello"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_write_file(app: FastAPI, client: AsyncClient, project: Project) -> None:

    response = await client.post(app.url_path_for("write_file", project_id=project.id, file_path="hello"),
                                 content=b"world")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    with open(os.path.join(project.path, "hello")) as f:
        assert f.read() == "world"

    response = await client.post(app.url_path_for("write_file", project_id=project.id, file_path="../hello"))
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_write_and_get_file_with_leading_slashes_in_filename(
        app: FastAPI,
        client: AsyncClient,
        project: Project) -> None:

    response = await client.post(app.url_path_for("write_file", project_id=project.id, file_path="//hello"),
                                 content=b"world")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await client.get(app.url_path_for("get_file", project_id=project.id, file_path="//hello"))
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"world"


async def test_import(app: FastAPI, client: AsyncClient, tmpdir, controller: Controller) -> None:

    with zipfile.ZipFile(str(tmpdir / "test.zip"), 'w') as myzip:
        myzip.writestr("project.gns3", b'{"project_id": "c6992992-ac72-47dc-833b-54aa334bcd05", "version": "2.0.0", "name": "test"}')
        myzip.writestr("demo", b"hello")

    project_id = str(uuid.uuid4())
    with open(str(tmpdir / "test.zip"), "rb") as f:
        response = await client.post(app.url_path_for("import_project", project_id=project_id), content=f.read())
    assert response.status_code == status.HTTP_201_CREATED

    project = controller.get_project(project_id)
    with open(os.path.join(project.path, "demo")) as f:
        content = f.read()
    assert content == "hello"


async def test_duplicate(app: FastAPI, client: AsyncClient, project: Project) -> None:

    response = await client.post(app.url_path_for("duplicate_project", project_id=project.id), json={"name": "hello"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "hello"
