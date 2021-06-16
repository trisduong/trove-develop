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
from requests.exceptions import ConnectionError
from sqlalchemy import desc
from swiftclient.client import ClientException

from trove.backup.state import BackupState
from trove.common import cfg
from trove.common import clients
from trove.common import constants
from trove.common import exception
from trove.common import swift
from trove.common import utils
from trove.common.i18n import _
from trove.datastore import models as datastore_models
from trove.db.models import DatabaseModelBase
from trove.quota.quota import run_with_quotas
from trove.taskmanager import api

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Metadata(object):

    @classmethod
    def list(cls, context, resource_type, resource_id):
        query = DBMetadata.query()
        filters = [
            DBMetadata.deleted == 0,
            DBMetadata.resource_id == resource_id,
            DBMetadata.resource_type == resource_type
        ]

        query = query.filter(*filters)
        return query

    @classmethod
    def get(cls, context, resource_type, resource_id, key):
        query = DBMetadata.query()
        filters = [
            DBMetadata.deleted == 0,
            DBMetadata.resource_id == resource_id,
            DBMetadata.resource_type == resource_type,
            DBMetadata.key == key
        ]

        query = query.filter(*filters)
        return query

    @classmethod
    def create(cls, context, resource_type, resource_id, key, value):
        """
        create db record for metadata
        :param cls:
        :param context: project_id included
        :param resource_type:
        :param resource_id:
        :param key:
        :param value:

        :return:
        """

        try:
            db_info = DBMetadata.create(
                resource_type=resource_type,
                resource_id=resource_id,
                tenant_id=context.project_id,
                key=key,
                value=value
            )
        except exception.InvalidModelError as ex:
            LOG.exception("Unable to create metadata record for "
                          "resource: %s with id: %s", resource_type,
                          resource_id)
            raise exception.MetadataCreationError(str(ex))

        return db_info

    @classmethod
    def delete(cls, context, resource_type, resource_id, key):
        """
        update Metadata table on deleted flag for given Metadata
        :param cls:
        :param context: context containing the tenant id and token
        :param resource_type: resource_type
        :param resource_id: resource_id
        :param key: key

        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
            key=key,
            deleted=False
        )
        query.delete()

        return

    @classmethod
    def edit(cls, context, resource_type, resource_id, key, value):
        """
        update Metadata table on deleted flag for given Metadata
        :param cls:
        :param context: context containing the tenant id and token
        :param resource_type: resource_type
        :param resource_id: resource_id
        :param key: key
        :param value: value

        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
            key=key,
            deleted=False
        )

        metadata = query.update(value)

        return metadata


class DBMetadata(DatabaseModelBase):
    """A table for metadata records."""
    _data_fields = ['id', 'resource_type', 'resource_id', 'project_id', 'key',
                    'value', 'created', 'deleted', 'deleted_at', 'updated']
    _table_name = 'metadata'


def persisted_models():
    return {'metadata': DBMetadata}
