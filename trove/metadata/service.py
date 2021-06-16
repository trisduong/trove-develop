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
            context,
            resource_type=resource_type,
            resource_id=resource_id
        )

        return wsgi.Result(views.MetadataViews(metadatas), 200)

    def show(self, req, tenant_id, resource_type, resource_id, key):
        """Show Metadata Item Details."""
        LOG.debug("Showing metadata item details for tenant %(tenant_id)s "
                  "Resource: '%(resource_type)s with ID: %(resource_id)s'",
                  {'tenant_id': tenant_id, 'resource_type': resource_type,
                   'resource_id': resource_id})
        context = req.environ[wsgi.CONTEXT_KEY]
        metadata = Metadata.get(
            context,
            resource_type=resource_type,
            resource_id=resource_id,
            key=key
        )
        policy.authorize_on_target(context, 'metadata:show',
                                   {'tenant': metadata['project_id']})
        return wsgi.Result(views.MetadataView(metadata).data(), 200)

    def create(self, req, body, tenant_id, resource_type, resource_id):
        LOG.info("Creating metadata items for tenant %s", tenant_id)
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:create')
        data = body['metadata']
        key = data.get('key')
        value = data.get('value')

        context.notification = notification.DBaaSMetadataCreate(
            context, request=req)

        with StartNotification(context, key=key, value=value,
                               resource_type=resource_type,
                               resource_id=resource_id):
            metadata = Metadata.create(
                context, resource_type=resource_type,
                resource_id=resource_id, key=key,
                value=value
            )

        return wsgi.Result(views.MetadataView(metadata).data(), 202)

    def delete(self, req, tenant_id, resource_type, resource_id, key):
        """Delete Metadata Item."""
        LOG.info("Deleting metadata item for tenant %(tenant_id)s Key: %(key)s"
                 " in Resource: '%(resource_type)s with ID: %(resource_id)s'",
                 {'tenant_id': tenant_id, 'key': key,
                  'resource_type': resource_type, 'resource_id': resource_id})

        context = req.environ[wsgi.CONTEXT_KEY]
        metadata = Metadata.get(
            context,
            resource_type=resource_type,
            resource_id=resource_id,
            key=key
        )
        policy.authorize_on_target(context, 'metadata:delete',
                                   {'tenant': metadata['project_id']})
        context.notification = notification.DBaaSMetadataDelete(context,
                                                                request=req)
        with StartNotification(context, key=key, resource_type=resource_type,
                               resource_id=resource_id):
            Metadata.delete(context, resource_type, resource_id, key)
        return wsgi.Result(None, 202)

    def edit(self, req, body, tenant_id, resource_type, resource_id, key):
        LOG.info("Update metadata for tenant %(tenant_id)s Key: %(key)s"
                 " in Resource: '%(resource_type)s with ID: %(resource_id)s'",
                 {'tenant_id': tenant_id, 'resource_type': resource_type,
                  'resource_id': resource_id, 'key': key})
        context = req.environ[wsgi.CONTEXT_KEY]
        metadata = Metadata.get(context, resource_type, resource_id, key)
        policy.authorize_on_target(context, 'metadata:edit',
                                   {'tenant': metadata['project_id']})
        data = body['metadata']
        value = data[key]
        context.notification = notification.DBaaSMetadataEdit(context,
                                                              request=req)
        with StartNotification(context, resource_type=resource_type,
                               resource_id=resource_id, key=key):
            metadata = Metadata.edit(
                context, resource_type, resource_id,
                key, value
            )

        return wsgi.Result(views.MetadataView(metadata).data(), 202)

    def update(self, req, body, tenant_id, resource_type, resource_id):
        LOG.info("Update metadata for tenant %(tenant_id)s in Resource: "
                 "'%(resource_type)s with ID: %(resource_id)s'",
                 {'tenant_id': tenant_id, 'resource_type': resource_type,
                  'resource_id': resource_id})
        context = req.environ[wsgi.CONTEXT_KEY]
        policy.authorize_on_tenant(context, 'metadata:update')
        data = body['metadata']
        metadatas = []
        context.notification = notification.DBaaSMetadataUpdate(context,
                                                                request=req)
        with StartNotification(context, resource_type=resource_type,
                               resource_id=resource_id):
            for key, value in data.items():
                metadata = Metadata.get(
                    context, resource_type, resource_id, key
                )
                if metadata:
                    policy.authorize_on_target(
                        context, 'metadata:update',
                        {'tenant': metadata['project_id']}
                    )

                    metadata = Metadata.edit(
                        context, resource_type, resource_id,
                        key, value
                    )
                else:
                    context.notification = notification.DBaaSMetadataCreate(
                        context, request=req)

                    with StartNotification(context, key=key, value=value,
                                           resource_type=resource_type,
                                           resource_id=resource_id):
                        metadata = Metadata.create(
                            context, resource_type=resource_type,
                            resource_id=resource_id, key=key,
                            value=value
                        )

                metadatas.append(metadata)

        return wsgi.Result(views.MetadataViews(metadatas).data(), 202)
