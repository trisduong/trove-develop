# Copyright 2021 OpenStack Foundation
# Copyright 2021 VCCorp.
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

from trove.metadata import views
from trove.metadata.models import Metadata
from trove.common import apischema
from trove.common import pagination
from trove.common import notification
from trove.common import policy
from trove.common import wsgi
from trove.common.notification import StartNotification

LOG = logging.getLogger(__name__)


class MetadataController(wsgi.Controller):
    """
    Controller for accessing metadata in the OpenStack API.
    """
    schemas = apischema.metadata

    def index(self, req, tenant_id, resource_type, resource_id):
        """
        List All Metadata.
        """
        LOG.debug("Listing all metadata for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:index')

        metadatas = Metadata.list(
            resource_type=resource_type,
            resource_id=resource_id
        )
        view = views.MetadataViews(metadatas)
        paged = pagination.SimplePaginatedDataView(req.url, 'metadatas', view,
                                                   None)

        return wsgi.Result(paged.data(), 200)

    def show(self, req, tenant_id, resource_type, resource_id, key):
        """Show Metadata Item Details."""
        LOG.debug("Showing metadata for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]

        metadata = Metadata.get(
            resource_type=resource_type,
            resource_id=resource_id,
            key=key
        )
        policy.authorize_on_target(context, 'metadata:show',
                                   {'tenant': metadata.project_id})

        return wsgi.Result(views.MetadataView(metadata).data(), 200)

    def create(self, req, body, tenant_id, resource_type, resource_id):
        LOG.info("Creating metadata items for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:create')
        data = body['metadata']

        context.notification = notification.DBaaSMetadataCreate(
            context, request=req)

        with StartNotification(
                context, data=data,
                resource_type=resource_type,
                resource_id=resource_id
        ):
            metadatas = Metadata.create(
                project_id=context.project_id,
                resource_type=resource_type,
                resource_id=resource_id,
                data=data
            )

        view = views.MetadataViews(metadatas)
        paged = pagination.SimplePaginatedDataView(req.url, 'metadatas', view,
                                                   None)

        return wsgi.Result(paged.data(), 200)

    def delete(self, req, tenant_id, resource_type, resource_id, key):
        """Delete Metadata Item."""
        LOG.debug("Deleting metadata for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]

        metadata = Metadata.get(
            resource_type=resource_type,
            resource_id=resource_id,
            key=key
        )
        policy.authorize_on_target(context, 'metadata:delete',
                                   {'tenant': metadata.project_id})

        context.notification = notification.DBaaSMetadataDelete(
            context, request=req)
        with StartNotification(
                context,
                key=key,
                resource_type=resource_type,
                resource_id=resource_id
        ):
            Metadata.delete(
                context.project_id, resource_type, resource_id, key
            )

        return wsgi.Result(None, 202)

    def edit(self, req, body, tenant_id, resource_type, resource_id, key):
        LOG.debug("Edit metadata for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:edit')

        data = body['metadata']
        value = data[key]

        context.notification = notification.DBaaSMetadataEdit(
            context, request=req)
        with StartNotification(
                context,
                resource_type=resource_type,
                resource_id=resource_id,
                key=key
        ):
            Metadata.edit(
                context.project_id, resource_type, resource_id, key, value
            )

        return wsgi.Result(None, 202)

    def update(self, req, body, tenant_id, resource_type, resource_id):
        LOG.debug("Update metadata for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:update')

        data = body['metadata']

        context.notification = notification.DBaaSMetadataUpdate(
            context, request=req)
        with StartNotification(
                context, resource_type=resource_type,
                resource_id=resource_id, data=data
        ):
            Metadata.update(
                context.project_id, resource_type, resource_id, data
            )

        return wsgi.Result(None, 202)
