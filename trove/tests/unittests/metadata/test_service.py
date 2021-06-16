# Copyright 2020 Catalyst Cloud
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
from unittest import mock

from trove.common import cfg
from trove.common import wsgi
from trove.common import exception
from trove.metadata import service
from trove.metadata import models as metadata_models
from trove.tests.unittests import trove_testtools
from trove.tests.unittests.util import util

CONF = cfg.CONF


class TestMetadatasController(trove_testtools.TestCase):
    @classmethod
    def setUpClass(cls):
        util.init_db()

        cls.project_id = cls.random_uuid()
        cls.resource_id = cls.random_uuid()
        cls.resource_type = 'resource_test'
        cls.data = {
            "test_init": {
                "test_bool": True,
                "test_list": [],
                "test_string": "string"
            }
        }
        cls.metadata = metadata_models.Metadata.create(
            project_id=cls.project_id,
            resource_id=cls.resource_id,
            resource_type=cls.resource_type,
            data=cls.data
        )
        cls.metadata_id = cls.metadata[0].id

        cls.controller = service.MetadataController()

        cls.req_mock = mock.MagicMock(
            environ={
                wsgi.CONTEXT_KEY: mock.MagicMock(project_id=cls.project_id)
            }
        )

        super(TestMetadatasController, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        util.cleanup_db()

        super(TestMetadatasController, cls).tearDownClass()

    def setUp(self):
        trove_testtools.patch_notifier(self)
        super(TestMetadatasController, self).setUp()

    def test_metadata_create(self):
        body = {
            "metadata": {
                "test_dict_create": {
                    "test_bool": True,
                    "test_list": [],
                    "test_string": "string"
                },
                "test_list": ["string_1", "string_2"],
                "test_string": "string"
            }
        }
        result = self.controller.create(
            self.req_mock, body, self.project_id,
            self.resource_type, self.resource_id
        )
        data = result.data(None).get('metadatas')

        self.assertEqual(3, len(data))

    def test_metadata_edit(self):
        body = {
            "metadata": {
                "test_init": {
                    "test_bool": True,
                    "test_list": [123456789, 987654321, 434343232],
                    "test_string": "string_edited"
                }
            }
        }
        self.controller.edit(
            self.req_mock, body, self.project_id, self.resource_type,
            self.resource_id, "test_init"
        )
        result = self.controller.show(
            self.req_mock, self.project_id, self.resource_type,
            self.resource_id, "test_init"
        )
        data = result.data(None).get('metadata')

        expected = {
            "id": self.metadata_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "project_id": self.project_id,
            "test_init": {
                "test_bool": True,
                "test_list": [123456789, 987654321, 434343232],
                "test_string": "string_edited"
            }
        }

        self.assertDictContains(data, expected)

    def test_metadata_delete(self):
        self.controller.delete(
            self.req_mock, self.project_id, self.resource_type,
            self.resource_id, "test_dict_create"
        )
        self.assertRaises(
            exception.MetadataKeyForResourceNotFound,
            self.controller.show,
            self.req_mock, self.project_id, self.resource_type,
            self.resource_id, "test_dict_create"
        )

    def test_metadata_index(self):
        result = self.controller.index(
            self.req_mock, self.project_id,
            self.resource_type, self.resource_id
        )
        data = result.data(None).get('metadatas')
        self.assertEqual(3, len(data))

    def test_metadata_show(self):
        result = self.controller.show(
            self.req_mock, self.project_id, self.resource_type,
            self.resource_id, "test_init"
        )
        data = result.data(None).get('metadata')

        expected = {
            "id": self.metadata_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "project_id": self.project_id,
            "test_init": {
                "test_bool": True,
                "test_list": [123456789, 987654321, 434343232],
                "test_string": "string_edited"
            }
        }

        self.assertDictContains(data, expected)

    def test_metadata_update(self):
        body = {
            "metadata": {
                "test_list": ["string_1", "string_2"],
                "test_create": "creating"
            }
        }
        self.controller.update(
            self.req_mock, body, self.project_id,
            self.resource_type, self.resource_id
        )
        result_edit = self.controller.show(
            self.req_mock, self.project_id, self.resource_type,
            self.resource_id, "test_list"
        )
        result_create = self.controller.show(
            self.req_mock, self.project_id, self.resource_type,
            self.resource_id, "test_create"
        )
        data_edit = result_edit.data(None).get('metadata')
        data_create = result_create.data(None).get('metadata')

        edit_expected = {
            "id": data_edit['id'],
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "project_id": self.project_id,
            "test_list": ["string_1", "string_2"]
        }
        create_expected = {
            "id": data_create['id'],
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "project_id": self.project_id,
            "test_create": "creating"
        }

        self.assertDictContains(data_edit, edit_expected)
        self.assertDictContains(data_create, create_expected)

    def test_metadata_key_existed(self):
        body = {
            "metadata": {
                "test_init": {
                    "key": "test_existed"
                }
            }
        }
        self.assertRaises(
            exception.MetadataKeyForResourceExist,
            self.controller.create,
            self.req_mock, body, self.project_id,
            self.resource_type, self.resource_id
        )
