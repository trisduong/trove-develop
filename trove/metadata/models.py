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


class DBMetadata(DatabaseModelBase):
    """A table for metadata records."""
    _data_fields = ['id', 'resource_type', 'resource_id', 'tenant_id',
                    'key', 'value', 'created', 'deleted',
                    'deleted_at', 'updated']
    _table_name = 'metadata'


def persisted_models():
        return {'metadata': DBMetadata}


class Metadata(object):

    @classmethod
    def create(cls, context, resource_type, resource_id, key, value):
        """
        create db record for metadata
        :param cls:
        :param context: tenant_id included
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
    def get_by_id(cls, context, id, deleted=False):
        """
        get the metadata for that id
        :param cls:
        :param context:
        :param id:
        :param deleted: Return deleted
        :return:
        """
        try:
            query = DBMetadata.find_by(context=context,
                                       id=id,
                                       deleted=deleted)
            return cls._paginate(context, query)
        except exception.MetadataNotFound:
            raise exception.MetadataNotFound(id=id)

    @classmethod
    def get_by_resource_id(cls, context, resource_id, deleted=False):
        """
        get the metadata for that id
        :param cls:
        :param context:
        :param resource_id:
        :param deleted: Return deleted
        :return:
        """
        try:
            query = DBMetadata.find_by(context=context,
                                       resource_id=resource_id,
                                       deleted=deleted)
            return cls._paginate(context, query)
        except exception.MetadataNotFound:
            raise exception.MetadataNotFound(resource_id=resource_id)

    @classmethod
    def _paginate(cls, context, query):
        """Paginate the results of the base query.
        We use limit/offset as the results need to be ordered by date
        and not the primary key.
        """
        marker = int(context.marker or 0)
        limit = int(context.limit or CONF.backups_page_size)
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
    def list(cls, context, project_id=None, resource_type=None, resource_id=None,
             all_projects=None):
        query = DBMetadata.query()
        filters = [DBMetadata.deleted == 0]

        if project_id:
            filters.append(DBMetadata.tenant_id == project_id)
        elif not all_projects:
            filters.append(DBMetadata.tenant_id == context.project_id)

        if resource_id:
            filters.append(DBMetadata.resource_id == resource_id)

        if resource_type:
            filters.append(DBMetadata.resource_type == resource_type)

        query = query.filter(*filters)
        return cls._paginate(context, query)

    @classmethod
    def list_for_resource_id(cls, context, resource_id):
        """
        list all live Backups associated with given instance
        :param cls:
        :param context:
        :param resource_id:
        :return:
        """
        query = DBMetadata.query()
        if context.is_admin:
            query = query.filter_by(resource_id=resource_id,
                                    deleted=False)
        else:
            query = query.filter_by(resource_id=resource_id,
                                    tenant_id=context.project_id,
                                    deleted=False)
        return cls._paginate(context, query)

    @classmethod
    def delete(cls, context, id):
        """
        update Metadata table on deleted flag for given Metadata
        :param cls:
        :param context: context containing the tenant id and token
        :param id: id
        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(id=id, deleted=False)

        def _delete_resources():
            query.delete()

        return _delete_resources

    @classmethod
    def delete_resource_metadatas(cls, context, resource_id):
        """
        update Metadata table on deleted flag for given Metadata
        :param cls:
        :param context: context containing the tenant id and token
        :param resource_id: resource_id
        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(resource_id=resource_id, deleted=False)

        def _delete_resources():
            query.delete()

        return _delete_resources

    @classmethod
    def edit(cls, context, id, data):
        """
        update Metadata table on deleted flag for given Metadata
        :param cls:
        :param context: context containing the tenant id and token
        :param id: id
        :param data: data
        :return:
        """

        query = DBMetadata.query()
        query = query.filter_by(id=id, deleted=False)

        def _update_resources():
            query.update(data)

        return _update_resources

