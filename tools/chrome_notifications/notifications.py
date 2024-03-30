#!/usr/bin/env python3
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
"""Parser for Chrome Notifications.

Usage:
$ pip install dfdatetime protobuf
$ python notifications.py <PLATFORM NOTIFICATIONS FOLDER>

"""
from __future__ import annotations
import json
import pathlib
import sys
import dataclasses

from typing import Any, Union

import notification_database_data_pb2 as notification_pb2

from dfdatetime import webkit_time
from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.leveldb import log
from dfindexeddb.leveldb import ldb

from google.protobuf.json_format import MessageToJson


@dataclasses.dataclass
class ChromeNotificationRecord:
  src_file: str = None
  offset: int = None
  key: str = None
  sequence_number: int = None
  type: int = None
  origin: str = None
  service_worker_registration_id: int = None
  notification_title: str = None
  notification_direction: str = None
  notification_lang: str = None
  notification_body: str = None
  notification_tag: str = None
  notification_icon: str = None
  notification_silent: bool = None
  notification_data: str = None
  notification_requireInteraction: bool = None
  notification_time: str = None
  notification_renotify: bool = None
  notification_badge: str = None
  notification_image: str = None
  notification_id: str = None
  replaced_existing_notification: bool = None
  num_clicks: int = None
  num_action_button_clicks: int = None
  creation_time: str = None
  closed_reason: str = None
  has_triggered: bool = None

  @classmethod
  def FromLeveldbRecord(
      cls,
      ldb_record: Union[log.ParsedInternalKey, ldb.KeyValueRecord]
  ) -> ChromeNotificationRecord:
    record = cls()
    record.offset = ldb_record.offset
    record.key = ldb_record.key.decode()
    record.sequence_number = ldb_record.sequence_number  
    record.type = ldb_record.record_type

    if not ldb_record.value:
      return record
        
    notification_proto = notification_pb2.NotificationDatabaseDataProto()
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
    record.notification_requireInteraction = (
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


def Main(indexeddb_path):
  for filename in pathlib.Path(indexeddb_path).iterdir():
    if filename.name.startswith('.'):
      continue
    if filename.name.endswith('.log'):
      leveldb_records = list(
          log.FileReader(filename.as_posix()).GetParsedInternalKeys())
    elif filename.name.endswith('.ldb'):
      leveldb_records = list(
          ldb.FileReader(filename.as_posix()).GetKeyValueRecords())
    else:
      continue

    for record in leveldb_records:
      notification_record = ChromeNotificationRecord.FromLeveldbRecord(record)
      notification_record.src_file = filename.as_posix()
      print(json.dumps(dataclasses.asdict(notification_record), indent=2))


if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: python notifications.py <PLATFORM NOTIFICATIONS FOLDER>")
    sys.exit(1)
  Main(sys.argv[1])
