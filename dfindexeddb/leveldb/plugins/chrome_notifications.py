# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parser plugin for Chrome Notifications."""
from __future__ import annotations

import dataclasses
import logging

from typing import Optional

try:
  # pytype: disable=import-error
  from dfdatetime import webkit_time
  from dfindexeddb.leveldb.plugins import notification_database_data_pb2 as \
      notification_pb2
  # pytype: enable=import-error
  _has_import_dependencies = True
except ImportError as err:
  _has_import_dependencies = False
  logging.warning((
      'Could not import dependencies for '
      'leveldb.plugins.chrome_notifications: %s'), err)

from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.leveldb.plugins import interface
from dfindexeddb.leveldb.plugins import manager


@dataclasses.dataclass
class ChromeNotificationRecord(interface.LeveldbPlugin):
  """Chrome notification record."""
  src_file: Optional[str] = None
  offset: Optional[int] = None
  key: Optional[str] = None
  sequence_number: Optional[int] = None
  type: Optional[int] = None
  origin: Optional[str] = None
  service_worker_registration_id: Optional[int] = None
  notification_title: Optional[str] = None
  notification_direction: Optional[str] = None
  notification_lang: Optional[str] = None
  notification_body: Optional[str] = None
  notification_tag: Optional[str] = None
  notification_icon: Optional[str] = None
  notification_silent: Optional[bool] = None
  notification_data: Optional[str] = None
  notification_require_interaction: Optional[bool] = None
  notification_time: Optional[str] = None
  notification_renotify: Optional[bool] = None
  notification_badge: Optional[str] = None
  notification_image: Optional[str] = None
  notification_id: Optional[str] = None
  replaced_existing_notification: Optional[bool] = None
  num_clicks: Optional[int] = None
  num_action_button_clicks: Optional[int] = None
  creation_time: Optional[str] = None
  closed_reason: Optional[str] = None
  has_triggered: Optional[bool] = None

  @classmethod
  def FromKeyValueRecord(
      cls,
      ldb_record
  ) -> ChromeNotificationRecord:
    record = cls()
    record.offset = ldb_record.offset
    record.key = ldb_record.key.decode()
    record.sequence_number = ldb_record.sequence_number
    record.type = ldb_record.record_type

    if not ldb_record.value:
      return record

    # pylint: disable-next=no-member,line-too-long
    notification_proto = notification_pb2.NotificationDatabaseDataProto()  # pytype: disable=module-attr
    notification_proto.ParseFromString(ldb_record.value)

    record.origin = notification_proto.origin
    record.service_worker_registration_id = (
        notification_proto.service_worker_registration_id)
    record.notification_title = notification_proto.notification_data.title
    record.notification_direction = (
        notification_proto.notification_data.direction)
    record.notification_lang = notification_proto.notification_data.lang
    record.notification_body = notification_proto.notification_data.body
    record.notification_tag = notification_proto.notification_data.tag
    record.notification_icon = notification_proto.notification_data.icon
    record.notification_silent = notification_proto.notification_data.silent
    record.notification_data = notification_proto.notification_data.data
    record.notification_require_interaction = (
        notification_proto.notification_data.require_interaction)
    record.notification_time = webkit_time.WebKitTime(
        timestamp=notification_proto.notification_data.timestamp
    ).CopyToDateTimeString()
    record.notification_renotify = notification_proto.notification_data.renotify
    record.notification_badge = notification_proto.notification_data.badge
    record.notification_image = notification_proto.notification_data.image
    record.notification_id = notification_proto.notification_id
    record.replaced_existing_notification = (
        notification_proto.replaced_existing_notification)
    record.num_clicks = notification_proto.num_clicks
    record.num_action_button_clicks = (
        notification_proto.num_action_button_clicks)
    record.creation_time = webkit_time.WebKitTime(
        timestamp=notification_proto.creation_time_millis
    ).CopyToDateTimeString()
    record.closed_reason = notification_proto.closed_reason
    record.has_triggered = notification_proto.has_triggered

    if not notification_proto.notification_data.data:
      return record

    notification_data = blink.V8ScriptValueDecoder(
        raw_data=notification_proto.notification_data.data).Deserialize()
    record.notification_data = notification_data

    return record


# check if dependencies are in existence..

if _has_import_dependencies:
  manager.PluginManager.RegisterPlugin(ChromeNotificationRecord)
