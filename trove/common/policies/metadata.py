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

from oslo_policy import policy

from trove.common.policies import base

rules = [
    policy.DocumentedRuleDefault(
        name='metadata:index',
        check_str='rule:admin_or_owner',
        description='List All Metadata.',
        operations=[
            {
                'path': base.PATH_METADATAS,
                'method': 'GET'
            }
        ]),
    policy.DocumentedRuleDefault(
        name='metadata:create',
        check_str='rule:admin_or_owner',
        description='Create or Update Metadata Items.',
        operations=[
            {
                'path': base.PATH_METADATAS,
                'method': 'POST'
            }
        ]),
    policy.DocumentedRuleDefault(
        name='metadata:update',
        check_str='rule:admin_or_owner',
        description='Replace Metadata Items.',
        operations=[
            {
                'path': base.PATH_METADATAS,
                'method': 'PUT'
            }
        ]),
    policy.DocumentedRuleDefault(
        name='metadata:show',
        check_str='rule:admin_or_owner',
        description='Show Metadata Item Details.',
        operations=[
            {
                'path': base.PATH_METADATA,
                'method': 'GET'
            }
        ]),
    policy.DocumentedRuleDefault(
        name='metadata:delete',
        check_str='rule:admin_or_owner',
        description='Delete Metadata Item.',
        operations=[
            {
                'path': base.PATH_METADATA,
                'method': 'DELETE'
            }
        ]),
    policy.DocumentedRuleDefault(
        name='metadata:edit',
        check_str='rule:admin_or_owner',
        description='Create Or Update Metadata Item.',
        operations=[
            {
                'path': base.PATH_METADATA,
                'method': 'PUT'
            }
        ]),
]


def list_rules():
    return rules
