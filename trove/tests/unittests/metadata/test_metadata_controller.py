# Copyright 2014 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
import jsonschema

from trove.metadata.service import MetadataController
from trove.tests.unittests import trove_testtools


class TestMetadataController(trove_testtools.TestCase):

    def setUp(self):
        super(TestMetadataController, self).setUp()
        self.controller = MetadataController()

    def _test_validate_metadata_with_action(
            self, body, action, is_valid=True):
        schema = self.controller.get_schema(action, body)
        self.assertIsNotNone(schema)
        validator = jsonschema.Draft4Validator(schema)
        if is_valid:
            self.assertTrue(validator.is_valid(body))
        else:
            self.assertFalse(validator.is_valid(body))
            errors = sorted(validator.iter_errors(body), key=lambda e: e.path)
            error_messages = [error.message for error in errors]
            return error_messages

    def test_validate_create_metadata(self):
        body = {
            "metadata": {
                "ids": [],
                "name": "test",
                "failover": {
                    "instance-1": True,
                    "instance-2": False
                }
            }
        }
        self._test_validate_metadata_with_action(body, action='create')

    def test_validate_create_invalid_param(self):
        body = {
            "metadatas": {
                "failover": {
                    "instance-1": True,
                    "instance-2": False
                }
            }
        }
        error_messages = (
            self._test_validate_metadata_with_action(
                body, action='create', is_valid=False))
        self.assertIn("'metadata' is a required property", error_messages)

    def test_validate_create_invalid_param_length(self):
        body = {
            "metadata": {
                "key": "",
                "value": "invalid_length"
            }
        }
        error_messages = (
            self._test_validate_metadata_with_action(
                body, action='create', is_valid=False))
        self.assertIn("'' is too short", error_messages)

    def test_validate_edit_metadata(self):
        body = {
            "metadata": {
                "ids": ["id-2"],
                "name": "test-2",
                "failover": {
                    "instance-1": False,
                    "instance-2": False
                }
            }
        }
        self._test_validate_metadata_with_action(body, action="edit")

    def test_validate_update_metadata(self):
        body = {
            "metadata": {
                "ids": ["id-3"],
                "name": "test-3",
                "failover": {
                    "instance-1": True,
                    "instance-2": True
                }
            }
        }
        self._test_validate_metadata_with_action(body, action="update")
