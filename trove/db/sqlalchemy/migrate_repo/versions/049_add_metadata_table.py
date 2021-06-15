# Copyright 2020 Catalyst Cloud
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

from sqlalchemy.schema import Column
from sqlalchemy.schema import Index
from sqlalchemy.schema import MetaData
from sqlalchemy.schema import UniqueConstraint

from trove.db.sqlalchemy.migrate_repo.schema import BigInteger
from trove.db.sqlalchemy.migrate_repo.schema import Boolean
from trove.db.sqlalchemy.migrate_repo.schema import DateTime
from trove.db.sqlalchemy.migrate_repo.schema import String
from trove.db.sqlalchemy.migrate_repo.schema import Table
from trove.db.sqlalchemy.migrate_repo.schema import create_tables

meta = MetaData()

metadata = Table(
    'metadata',
    meta,
    Column('id', String(36), primary_key=True, nullable=False),
    Column('resource_id', String(36), nullable=False),
    Column('resource_type', String(255)),
    Column('project_id', String(36), nullable=False),
    Column('key', String(255)),
    Column('value', String(255)),
    Column('created', DateTime()),
    Column('updated', DateTime()),
    Column('deleted_at', DateTime()),
    Column('deleted', Boolean()),
    UniqueConstraint(
        'project_id', 'resource_id',
        name='UQ_metadata_project_id_resource_id'
    ),
    Index("metadata_project_id_resource_id", "project_id", "resource_id"),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    create_tables([metadata])
