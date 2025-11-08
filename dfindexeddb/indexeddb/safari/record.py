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
import plistlib
import sqlite3
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Generator, Optional

from dfindexeddb import errors
from dfindexeddb.indexeddb.safari import webkit


@dataclass
class ObjectStoreInfo:
  """An ObjectStoreInfo.

  Attributes:
    id: the object store ID.
    name: the object store name.
    key_path: the object store key path.
    auto_inc: True if the object store uses auto incrementing IDs.
    database_name: the database name from the IDBDatabaseInfo table.
  """

  id: int
  name: str
  key_path: str
  auto_inc: bool
  database_name: str


@dataclass
class IndexedDBRecord:
  """A Safari IndexedDBRecord.

  Attributes:
    key: the parsed key.
    value: the parsed value.
    object_store_id: the object store id.
    object_store_name: the object store name from the ObjectStoreInfo table.
    database_name: the IndexedDB database name from the IDBDatabaseInfo table.
    record_id: the record ID from the Record table.
  """

  key: Any
  value: Any
  object_store_id: int
  object_store_name: str
  database_name: str
  record_id: int


class FileReader:
  """A reader for Safari IndexedDB sqlite3 files.

  Attributes:
    database_name: the database name.
    database_version: the database version.
    metadata_version: the metadata version.
    max_object_store_id: the maximum object store ID.
  """

  def __init__(self, filename: str):
    """Initializes the FileReader.

    Args:
      filename: the IndexedDB filename.
    """
    self.filename = filename

    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "DatabaseVersion"'
      )
      result = cursor.fetchone()
      self.database_version = result[0]

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "MetadataVersion"'
      )
      result = cursor.fetchone()
      self.metadata_version = result[0]

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "DatabaseName"'
      )
      result = cursor.fetchone()
      self.database_name = result[0]

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "MaxObjectStoreID"'
      )
      result = cursor.fetchone()
      self.max_object_store_id = result[0]

  def ObjectStores(self) -> Generator[ObjectStoreInfo, None, None]:
    """Returns the Object Store information from the IndexedDB database.

    Yields:
      ObjectStoreInfo instances.
    """
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      cursor = conn.execute(
          "SELECT id, name, keypath, autoinc FROM ObjectStoreInfo"
      )
      results = cursor.fetchall()
      for result in results:
        key_path = plistlib.loads(result[2])
        yield ObjectStoreInfo(
            id=result[0],
            name=result[1],
            key_path=key_path,
            auto_inc=result[3],
            database_name=self.database_name,
        )

  def RecordById(self, record_id: int) -> Optional[IndexedDBRecord]:
    """Returns an IndexedDBRecord for the given record_id.

    Returns:
      the IndexedDBRecord or None if the record_id does not exist in the
          database.
    """
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, r.recordID FROM "
          "Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id "
          "WHERE r.recordID = ?",
          (record_id,),
      )
      row = cursor.fetchone()
      if not row:
        return None
      key = webkit.IDBKeyData.FromBytes(row[0]).data
      value = webkit.SerializedScriptValueDecoder.FromBytes(row[1])
      return IndexedDBRecord(
          key=key,
          value=value,
          object_store_id=row[2],
          object_store_name=row[3].decode("utf-8"),
          database_name=self.database_name,
          record_id=row[4],
      )

  def RecordsByObjectStoreName(
      self, name: str
  ) -> Generator[IndexedDBRecord, None, None]:
    """Returns IndexedDBRecords for the given ObjectStore name.

    Yields:
      IndexedDBRecord instances.
    """
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      for row in conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, r.recordID FROM "
          "Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id "
          "WHERE o.name = ?",
          (name,),
      ):
        key = webkit.IDBKeyData.FromBytes(row[0]).data
        value = webkit.SerializedScriptValueDecoder.FromBytes(row[1])
        yield IndexedDBRecord(
            key=key,
            value=value,
            object_store_id=row[2],
            object_store_name=row[3].decode("utf-8"),
            database_name=self.database_name,
            record_id=row[4],
        )

  def RecordsByObjectStoreId(
      self, object_store_id: int
  ) -> Generator[IndexedDBRecord, None, None]:
    """Returns IndexedDBRecords for the given ObjectStore id.

    Yields:
      IndexedDBRecord instances.
    """
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, r.recordID "
          "FROM Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id "
          "WHERE o.id = ?",
          (object_store_id,),
      )
      for row in cursor:
        key = webkit.IDBKeyData.FromBytes(row[0]).data
        value = webkit.SerializedScriptValueDecoder.FromBytes(row[1])
        yield IndexedDBRecord(
            key=key,
            value=value,
            object_store_id=row[2],
            object_store_name=row[3].decode("utf-8"),
            database_name=self.database_name,
            record_id=row[4],
        )

  def Records(self) -> Generator[IndexedDBRecord, None, None]:
    """Returns all the IndexedDBRecords."""
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, r.recordID "
          "FROM Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id"
      )
      for row in cursor:
        try:
          key = webkit.IDBKeyData.FromBytes(row[0]).data
        except (
            errors.ParserError,
            errors.DecoderError,
            NotImplementedError,
        ) as err:
          print(f"Error parsing IndexedDB key: {err}", file=sys.stderr)
          print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
          continue
        try:
          value = webkit.SerializedScriptValueDecoder.FromBytes(row[1])
        except (
            errors.ParserError,
            errors.DecoderError,
            NotImplementedError,
        ) as err:
          print(f"Error parsing IndexedDB value: {err}", file=sys.stderr)
          print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
          continue
        yield IndexedDBRecord(
            key=key,
            value=value,
            object_store_id=row[2],
            object_store_name=row[3].decode("utf-8"),
            database_name=self.database_name,
            record_id=row[4],
        )
