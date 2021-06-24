# Copyright 2021 Bizflycloud.

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

from sqlalchemy import desc

from trove.common import cfg
from trove.common import exception
from trove.db.models import DatabaseModelBase

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Metadata(object):

    @classmethod
    def list(cls, project_id, context=None, resource_type=None,
             resource_id=None, key=None, value=None, all_projects=None,
             exclude=False):
        """
        List All Metadata Records.
        :param cls:
        :param project_id: tenant_id
        :param context:
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param key: ID of resource
        :param value: ID of resource
        :param all_projects: option
        :param exclude: exclude

        :return:
        """

        query = DBMetadata.query()
        filters = [DBMetadata.deleted == 0]

        if not all_projects:
            filters.append(DBMetadata.project_id == project_id)
        if resource_id:
            filters.append(DBMetadata.resource_id == resource_id)
        if resource_type:
            filters.append(DBMetadata.resource_type == resource_type)
        if key:
            filters.append(DBMetadata.key == key)
        if value:
            filters.append(DBMetadata.value == value)

        query = query.filter(*filters)

        if exclude:
            dict_metadata = {}
            metadatas = query.all()
            for metadata in metadatas:
                dict_metadata.update(
                    {metadata.key: json.loads(metadata.value)})
            return dict_metadata

        return cls._paginate(context, query)

    @classmethod
    def get(cls, project_id, resource_type, resource_id, key):
        """
        Show Metadata Item Details Records.
        :param cls:
        :param project_id: tenant_id
        :param resource_type: TYPE of resource
        :param resource_id: ID of resource
        :param key: metadata key

        :return:
        """

        try:
            return DBMetadata.find_by(
                deleted=False,
                project_id=project_id,
                resource_id=resource_id,
                resource_type=resource_type,
                key=key)

        except exception.NotFound:
            raise exception.MetadataKeyForResourceNotFound(
                key=key,
                resource_type=resource_type,
                resource_id=resource_id)

    @classmethod
    def _paginate(cls, context, query):
        """
        Paginate the results of the base query.
        We use limit/offset as the results need to be ordered by date
        and not the primary key.
        """
        marker = int(context.marker or 0)
        limit = int(context.limit or CONF.metadatas_page_size)
        # order by 'updated DESC' to show the most recent backups first
        query = query.order_by(desc(DBMetadata.updated))
        # Apply limit/offset
        query = query.limit(limit)
        query = query.offset(marker)
        # check if we need to send a marker for the next page
        if query.count() < limit:
            marker = None
        else:
            marker += limit
        return query.all(), marker

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
                    project_id=project_id,
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
    def delete(cls, project_id, resource_type, resource_id, key=None):
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
        filters = [DBMetadata.deleted == 0,
                   DBMetadata.resource_type == resource_type,
                   DBMetadata.resource_id == resource_id,
                   DBMetadata.project_id == project_id]

        if key:
            filters.append(DBMetadata.key == key)

        query = query.filter(*filters)
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
                project_id=project_id,
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
