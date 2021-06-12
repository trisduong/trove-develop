# Copyright 2013 OpenStack Foundation
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from oslo_log import log as logging
from oslo_utils import strutils

from trove.metadata import views
from trove.metadata.models import Metadata
from trove.common import apischema
from trove.common import notification
from trove.common import pagination
from trove.common import policy
from trove.common import wsgi
from trove.common.notification import StartNotification

LOG = logging.getLogger(__name__)


class MetadataController(wsgi.Controller):
    """
    Controller for accessing metadata in the OpenStack API.
    """

    def index(self, req, tenant_id):
        """
        Return all metadata information for a tenant ID.
        """
        LOG.debug("Listing metadata for tenant %s", tenant_id)
        resource_type = req.GET.get('resource_type')
        resource_id = req.GET.get('resource_id')
        project_id = req.GET.get('project_id')
        all_projects = strutils.bool_from_string(req.GET.get('all_projects'))
        context = req.environ[wsgi.CONTEXT_KEY]

        if project_id or all_projects:
            policy.authorize_on_tenant(context, 'metadata:index:all_projects')
        else:
            policy.authorize_on_tenant(context, 'metadata:index')

        metadatas, marker = Metadata.list(
            context,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            all_projects=all_projects
        )
        view = views.MetadataViews(metadatas)
        paged = pagination.SimplePaginatedDataView(req.url, 'metadatas', view,
                                                   marker)
        return wsgi.Result(paged.data(), 200)

    def show(self, req, tenant_id, id):
        """Return metadata by key."""
        LOG.debug("Showing a metadata for tenant %(tenant_id)s ID: "
                  "'%(id)s'",
                  {'tenant_id': tenant_id, 'id': id})
        context = req.environ[wsgi.CONTEXT_KEY]
        metadata = Metadata.get_by_id(context, id)
        policy.authorize_on_target(context, 'metadata:show',
                                   {'tenant': metadata.tenant_id})
        return wsgi.Result(views.MetadataView(metadata).data(), 200)

    def create(self, req, body, tenant_id):
        LOG.info("Creating a metadata for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:create')
        data = body['metadata']
        key = data.get('key')
        value = data.get('value')
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')

        context.notification = notification.DBaaSMetadataCreate(
            context, request=req)

        with StartNotification(context, key=key, value=value,
                               resource_type=resource_type,
                               resource_id=resource_id):
            backup = Metadata.create(
                context, resource_type=resource_type,
                resource_id=resource_id, key=key,
                value=value
            )

        return wsgi.Result(views.MetadataView(backup).data(), 202)

    def delete(self, req, tenant_id, id):
        """Delete a single metadata."""
        LOG.info('Deleting metadata for tenant %(tenant_id)s '
                 'ID: %(id)s',
                 {'tenant_id': tenant_id, 'id': id})
        context = req.environ[wsgi.CONTEXT_KEY]
        metadata = Metadata.get_by_id(context, id)
        policy.authorize_on_target(context, 'metadata:delete',
                                   {'tenant': metadata.tenant_id})
        context.notification = notification.DBaaSMetadataDelete(context,
                                                                request=req)
        with StartNotification(context, id=id):
            Metadata.delete(context, id)
        return wsgi.Result(None, 202)

    def delete_resource_metadatas(self, req, tenant_id, resource_id):
        """Delete metadatas for a resource."""
        LOG.info('Deleting metadata for tenant %(tenant_id)s '
                 'resource_id: %(resource_id)s',
                 {'tenant_id': tenant_id, 'resource_id': resource_id})
        context = req.environ[wsgi.CONTEXT_KEY]
        metadatas = Metadata.get_by_resource_id(context, resource_id)
        for metadata in metadatas:
            policy.authorize_on_target(context, 'metadata:delete',
                                       {'tenant': metadata.tenant_id})
        context.notification = notification.DBaaSResourceMetadatasDelete(
            context,
            request=req
        )
        with StartNotification(context, resource_id=resource_id):
            Metadata.delete_resource_metadatas(context, resource_id)
        return wsgi.Result(None, 202)

    def edit(self, req, body, tenant_id, id):
        LOG.info('Update metadata for tenant %(tenant_id)s '
                 'ID: %(id)s',
                 {'tenant_id': tenant_id, 'id': id})
        context = req.environ[wsgi.CONTEXT_KEY]
        metadata = Metadata.get_by_id(context, id)
        policy.authorize_on_target(context, 'metadata:update',
                                   {'tenant': metadata.tenant_id})
        data = body['metadata']
        context.notification = notification.DBaaSMetadataUpdate(context,
                                                                request=req)
        with StartNotification(context, id=id):
            Metadata.edit(context, id, data)
        return wsgi.Result(None, 202)
