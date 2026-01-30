# -*- coding: utf-8 -*-
# Copyright 2026 Google LLC
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
"""Chromium IndexedDB records encoded in sqlite3 databases."""

import sqlite3
import zstd
from typing import Any, Generator, Optional
from dataclasses import dataclass

from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.indexeddb.chromium import record


@dataclass
class ChromiumIndexedDBRecord:
  """Chromium IndexedDB record parsed from sqlite3 database.

  Attributes:
    row_id: the row ID.
    object_store_id: the object store ID.
    compression_type: the compression type.
    key: the key.
    value: the value.
    raw_key: the raw key.
    raw_value: the raw value.
  """

  row_id: int
  object_store_id: int
  compression_type: int
  key: Any
  value: Any
  raw_key: Optional[bytes]
  raw_value: Optional[bytes]


@dataclass
class ChromiumObjectStoreInfo:
  """Chromium IndexedDB object store info parsed from sqlite3 database.

  Attributes:
    id: the object store ID.
    name: the object store name.
    key_path: the object store key path.
    auto_increment: whether the object store is auto increment.
    key_generator_current_number: the current number of the key generator.
  """

  id: int
  name: str
  key_path: str
  auto_increment: int
  key_generator_current_number: int


class DatabaseReader:
  """A reader for Chromium IndexedDB sqlite3 files."""

  def __init__(self, filename: str):
    """Initializes the reader.

    Args:
      filename: the path to the sqlite3 file.
    """
    self._filename = filename

  def ObjectStores(self) -> Generator[ChromiumObjectStoreInfo, None, None]:
    """Yields object stores."""
    with sqlite3.connect(self._filename) as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM object_stores")
      for row in cursor:
        yield ChromiumObjectStoreInfo(
            id=row[0],
            name=row[1].decode("utf-16-le"),
            key_path=row[2],
            auto_increment=row[3],
            key_generator_current_number=row[4],
        )

  def _EnumerateCursor(
      self,
      cursor: sqlite3.Cursor,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields records from a sqlite3 cursor.

    Args:
      cursor: the sqlite3 cursor.
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.

    Yields:
      ChromiumIndexedDBRecord records.
    """
    for row in cursor:
      raw_key, raw_value = row[3], row[4]
      key, value = None, None
      if raw_key and parse_key:
        key = record.SortableIDBKey.FromBytes(raw_data=raw_key, base_offset=0)
        if key and parse_value:
          if row[2] == 0:
            value = blink.V8ScriptValueDecoder.FromBytes(raw_value)
          else:
            value = blink.V8ScriptValueDecoder.FromBytes(
                zstd.decompress(raw_value)
            )

      yield ChromiumIndexedDBRecord(
          row_id=row[0],
          object_store_id=row[1],
          compression_type=row[2],
          key=key,
          value=value,
          raw_key=raw_key if include_raw_data else None,
          raw_value=raw_value if include_raw_data else None,
      )

  def RecordsByObjectStoreId(
      self,
      object_store_id: int,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields records for a given object store ID.

    Args:
      object_store_id: the object store ID.
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.
    """
    with sqlite3.connect(self._filename) as conn:
      cursor = conn.cursor()
      cursor.execute(
          "SELECT row_id, object_store_id, compression_type, key, value "
          "FROM records WHERE object_store_id = ?",
          (object_store_id,),
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, parse_key, parse_value
      )

  def RecordsByObjectStoreName(
      self,
      object_store_name: str,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields records for a given object store name.

    Args:
      object_store_name: the object store name.
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.
    """
    with sqlite3.connect(self._filename) as conn:
      cursor = conn.cursor()
      cursor.execute(
          "SELECT row_id, object_store_id, compression_type, key, value "
          "FROM records WHERE object_store_id = ?",
          (object_store_name,),
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, parse_key, parse_value
      )

  def Records(
      self,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields records.

    Args:
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.

    Yields:
      records.
    """
    with sqlite3.connect(self._filename) as conn:
      cursor = conn.cursor()
      cursor.execute(
          "SELECT row_id, object_store_id, compression_type, key, value "
          "FROM records"
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, parse_key, parse_value
      )
