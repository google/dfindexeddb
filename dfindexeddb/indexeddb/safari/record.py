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
"""Safari IndexedDB records."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
import plistlib
import sqlite3
from typing import Any, Generator, Union

from dfindexeddb import errors
from dfindexeddb import utils
from dfindexeddb.indexeddb.safari import ssv

SIDBKeyVersion = 0x00


class SIDBKeyType(enum.IntEnum):
  """SIDBKeyType."""
  MIN = 0x00
  NUMBER = 0x20
  DATE = 0x40
  STRING = 0x60
  BINARY = 0x80
  ARRAY = 0xA0
  MAX = 0xFF


@dataclass
class IDBKeyData(utils.FromDecoderMixin):
  """An IDBKeyData.

  Attributes:
    offset: the offset at which the IDBKeyData was parsed.
    key_type: the IDB Key Type

  """
  offset: int
  key_type: SIDBKeyType
  data: Union[float, datetime, str, bytes, list]

  @classmethod
  def FromDecoder(
      cls, decoder: utils.StreamDecoder, base_offset: int = 0) -> IDBKeyData:
    """Decodes an IDBKeyData from the current position of decoder.

    Refer to IDBSerialization.cpp

    Args:
      decoder: the decoder

    Returns:
      the IDBKeyData.

    Raises:
      ParserError: when SIDBKeyVersion is not found.
    """
    def _DecodeKeyBuffer(key_type):
      if key_type == SIDBKeyType.MIN:
        data = None
      if key_type == SIDBKeyType.NUMBER:
        _, data = decoder.DecodeDouble()
      elif key_type == SIDBKeyType.DATE:
        _, timestamp = decoder.DecodeDouble()
        data = datetime.fromtimestamp(timestamp/1000)  # UTC?
      elif key_type == SIDBKeyType.STRING:
        _, length = decoder.DecodeUint32()
        data = []
        _, raw_data = decoder.ReadBytes(length*2)
        data = raw_data.decode('utf-16-le')
      elif key_type == SIDBKeyType.BINARY:
        _, length = decoder.DecodeUint32()
        _, data = decoder.ReadBytes(length)
      elif key_type == SIDBKeyType.ARRAY:
        _, length = decoder.DecodeUint64()
        data = []
        for _ in range(length):
          _, key_type = decoder.DecodeUint8()
          element = _DecodeKeyBuffer(key_type)
          data.append(element)
      else:
        raise errors.ParserError('Unknown SIDBKeyType found')
      return data

    offset, version_header = decoder.DecodeUint8()
    _, key_type = decoder.DecodeUint8()

    # "Old-style key is characterized by this magic character that
    # begins serialized PropertyLists
    if key_type == b'b':
      pass  # TODO: handle this
    if version_header != SIDBKeyVersion:
      raise errors.ParserError('SIDBKeyVersion not found')

    data = _DecodeKeyBuffer(SIDBKeyType(key_type))
    return cls(
        offset=offset+base_offset,
        key_type=SIDBKeyType(key_type),
        data=data)


@dataclass
class ObjectStoreInfo:
  """An ObjectStoreInfo."""
  id: int
  name: str
  key_path: str
  auto_inc: bool


@dataclass
class IndexedDBRecord:
  """A Safari IndexedDBRecord."""
  key: Any
  value: Any
  object_store_id: int
  record_id: int


class FileReader:
  """A reader for Safari IndexedDB sqlite3 files."""

  def __init__(self, filename: str):
    self.filename = filename

    with sqlite3.connect(f'file:{self.filename}?mode=ro', uri=True) as conn:
      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "DatabaseVersion"')
      result = cursor.fetchone()
      self.database_version = result[0]

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "MetadataVersion"')
      result = cursor.fetchone()
      self.metadata_version = result[0]

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "DatabaseName"')
      result = cursor.fetchone()
      self.database_name = result[0]

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "MaxObjectStoreID"')
      result = cursor.fetchone()
      self.max_object_store_id = result[0]

  def ObjectStores(self) -> Generator[ObjectStoreInfo, None, None]:
    """Returns the Object Store information from the IndexedDB database."""
    with sqlite3.connect(f'file:{self.filename}?mode=ro', uri=True) as conn:
      cursor = conn.execute(
          'SELECT id, name, keypath, autoinc FROM ObjectStoreInfo')
      results = cursor.fetchall()
      for result in results:
        key_path = plistlib.loads(result[2])
        yield ObjectStoreInfo(
            id=result[0], name=result[1], key_path=key_path, auto_inc=result[3])

  def RecordsByObjectStoreName(
      self, name: str) -> Generator[IndexedDBRecord, None, None]:
    """Returns IndexedDBRecords for the given ObjectStore name."""
    with sqlite3.connect(f'file:{self.filename}?mode=ro', uri=True) as conn:
      conn.text_factory = bytes
      for row in conn.execute(
          'SELECT r.key, r.value, r.objectStoreID, r.recordID FROM Records r '
          'JOIN ObjectStoreInfo o ON r.objectStoreID == o.id '
          'WHERE o.name = ?', (name, )):
        key = IDBKeyData.FromBytes(row[0]).data
        value = ssv.SerializedScriptValueDecoder.FromBytes(row[1])
        yield IndexedDBRecord(
            key=key, value=value, object_store_id=row[2], record_id=row[3])

  def RecordsByObjectStoreId(
      self, object_store_id: int) -> Generator[IndexedDBRecord, None, None]:
    """Returns IndexedDBRecords for the given ObjectStore id."""
    with sqlite3.connect(self.filename) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          'SELECT r.key, r.value, r.objectStoreID, r.recordID FROM Records r '
          'JOIN ObjectStoreInfo o ON r.objectStoreID == o.id '
          'WHERE o.id = ?', (object_store_id, ))
      for row in cursor:
        key = IDBKeyData.FromBytes(row[0]).data
        value = ssv.SerializedScriptValueDecoder.FromBytes(row[1])
        yield IndexedDBRecord(
            key=key, value=value, object_store_id=row[2], record_id=row[3])

  def Records(self) -> Generator[IndexedDBRecord, None, None]:
    """Returns all the IndexedDBRecords."""
    with sqlite3.connect(self.filename) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          'SELECT r.key, r.value, r.objectStoreID, r.recordID FROM Records r '
          'JOIN ObjectStoreInfo o ON r.objectStoreID == o.id ')
      for row in cursor:
        key = IDBKeyData.FromBytes(row[0]).data
        value = ssv.SerializedScriptValueDecoder.FromBytes(row[1])
        yield IndexedDBRecord(
            key=key, value=value, object_store_id=row[2], record_id=row[3])
