# Copyright [2013] Hewlett-Packard Development Company, L.P.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Model classes that form the core of snapshots functionality."""

from oslo_log import log as logging
import json

from trove.common import cfg
from trove.common import exception
from trove.db.models import DatabaseModelBase

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Metadata(object):

    @classmethod
    def list(cls, resource_type, resource_id):
        """
        List All Metadata Records.
        :param cls:
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource

        :return:
        """

        query = DBMetadata.query()
        filters = [
            DBMetadata.deleted == 0,
            DBMetadata.resource_id == resource_id,
            DBMetadata.resource_type == resource_type
        ]

        query = query.filter(*filters)
        return query.all()

    @classmethod
    def get(cls, resource_type, resource_id, key):
        """
        Show Metadata Item Details Records.
        :param cls:
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param key: metadata key

        :return:
        """

        try:
            return DBMetadata.find_by(
                deleted=False,
                resource_id=resource_id,
                resource_type=resource_type,
                key=key)

        except exception.NotFound:
            raise exception.MetadataKeyForResourceNotFound(
                key=key,
                resource_type=resource_type,
                resource_id=resource_id)

    @classmethod
    def create(cls, project_id, resource_type, resource_id, data):
        """
        Create or Update Metadata Items Records.
        :param cls:
        :param project_id: project_id
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param data: metadata items

        :return:
        """

        metadatas = []

        for key, value in data.items():
            try:
                cls.get(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    key=key)
                raise exception.MetadataKeyForResourceExist(
                    key=key,
                    resource_type=resource_type,
                    resource_id=resource_id
                )
            except exception.NotFound:
                metadatas.append(DBMetadata.create(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    project_id=project_id,
                    key=key,
                    value=json.dumps(value)
                ))

        return metadatas

    @classmethod
    def delete(cls, project_id, resource_type, resource_id, key):
        """
        Delete Metadata Item Records.
        :param cls:
        :param project_id: project_id
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param key: metadata key

        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
            project_id=project_id,
            key=key,
            deleted=False
        )
        return query.update({"deleted": True})

    @classmethod
    def delete_all_for_resource(cls, project_id, resource_type, resource_id):
        """
        Delete Metadata Item Records.
        :param cls:
        :param project_id: project_id
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource

        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
            project_id=project_id,
            deleted=False
        )
        return query.update({"deleted": True})

    @classmethod
    def edit(cls, project_id, resource_type, resource_id, key, value):
        """
        Create Or Update Metadata Item Records.
        :param cls:
        :param project_id: project_id
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param key: metadata key
        :param value: metadata value

        :return:
        """

        try:
            cls.get(
                resource_type=resource_type,
                resource_id=resource_id,
                key=key
            )

            query = DBMetadata.query()
            query = query.filter_by(
                resource_type=resource_type,
                resource_id=resource_id,
                project_id=project_id,
                key=key,
                deleted=False
            )
            return query.update({"value": json.dumps(value)})

        except exception.NotFound:
            return DBMetadata.create(
                resource_type=resource_type,
                resource_id=resource_id,
                project_id=project_id,
                key=key,
                value=json.dumps(value)
            )

    @classmethod
    def update(cls, project_id, resource_type, resource_id, data):
        """
        Replace Metadata Items Records.
        :param cls:
        :param project_id: project_id
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param data: metadata items

        :return:
        """

        for key, value in data.items():
            cls.edit(
                resource_type=resource_type,
                resource_id=resource_id,
                project_id=project_id,
                key=key,
                value=value
            )


class DBMetadata(DatabaseModelBase):
    """A table for metadata records."""
    _data_fields = ['id', 'resource_type', 'resource_id', 'project_id', 'key',
                    'value', 'created', 'deleted', 'deleted_at', 'updated']
    _table_name = 'metadata'


def persisted_models():
    return {'metadata': DBMetadata}
