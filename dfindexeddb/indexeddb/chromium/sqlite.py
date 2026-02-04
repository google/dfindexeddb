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

import os
import sqlite3
from typing import Any, Generator, Optional
from dataclasses import dataclass

import snappy
import zstd

from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.indexeddb.chromium import definitions
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
    has_blobs: whether the record has blobs.
    raw_key: the raw key.
    raw_value: the raw value.
  """

  row_id: int
  object_store_id: int
  compression_type: int
  key: Any
  value: Any
  has_blobs: bool
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


@dataclass
class ChromiumBlobInfo:
  """Chromium IndexedDB blob info parsed from sqlite3 database.

  Attributes:
    row_id: the blob row ID.
    object_type: the object type.
    mime_type: the mime type.
    size_bytes: the total size in bytes.
    file_name: the file name (only for files).
    number_of_chunks: the number of chunks including the initial one.
    blob_data: the blob data.
  """

  row_id: int
  object_type: int
  mime_type: Optional[str]
  size_bytes: int
  file_name: Optional[str]
  number_of_chunks: int
  blob_data: bytes


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
      cursor.execute(definitions.SQL_OBJECT_STORES_QUERY)
      for row in cursor:
        yield ChromiumObjectStoreInfo(
            id=row[0],
            name=row[1].decode("utf-16-le"),
            key_path=row[2],
            auto_increment=row[3],
            key_generator_current_number=row[4],
        )

  def _GetLegacyBlobPath(self, blob_id: int) -> str:
    """Gets the path to a legacy blob file.

    Args:
      blob_id: the blob ID.

    Returns:
      The path to the legacy blob file.
    """
    base, ext = os.path.splitext(self._filename)
    db_dir = f"{base}_{ext}"
    return os.path.join(db_dir, f"{blob_id:x}")

  def LoadLegacyBlobData(self, blob_id: int) -> bytes:
    """Loads legacy blob data from disk.

    Args:
      blob_id: the blob ID.

    Returns:
      The blob data.

    Raises:
      FileNotFoundError: if the legacy blob file is not found.
    """
    blob_path = self._GetLegacyBlobPath(blob_id)
    if os.path.exists(blob_path):
      with open(blob_path, "rb") as f:
        return f.read()
    raise FileNotFoundError(f"Legacy blob file not found: {blob_path}")

  def LoadBlobDataForRecordId(
      self, row_id: int
  ) -> Generator[ChromiumBlobInfo, None, None]:
    """Loads blob data for a given record row ID.

    Args:
      row_id: the record row ID.

    Yields:
      ChromiumBlobInfo objects.
    """
    with sqlite3.connect(self._filename) as conn:
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()

      # Note this is a UNION query between the blob and overflow_blob_chunks
      # table.  The chunk_index = 0 for the row from the 'blobs' table.
      cursor.execute(definitions.SQL_BLOB_DATA_QUERY, (row_id, row_id))

      current_blob_id = None
      current_blob_data = bytearray()
      current_record: Optional[sqlite3.Row] = None
      total_number_of_chunks = 0

      for blob_row in cursor:
        blob_id = blob_row["row_id"]

        if blob_id != current_blob_id:
          if current_record is not None:
            yield ChromiumBlobInfo(
                row_id=current_record["row_id"],
                object_type=current_record["object_type"],
                mime_type=current_record["mime_type"],
                size_bytes=current_record["size_bytes"],
                file_name=current_record["file_name"],
                number_of_chunks=total_number_of_chunks,
                blob_data=bytes(current_blob_data),
            )
          current_blob_id = blob_id
          current_blob_data = bytearray()
          current_record = blob_row
          total_number_of_chunks = 0

        if blob_row["chunk_index"] == 0 and blob_row["bytes"] is None:
          current_blob_data.extend(self.LoadLegacyBlobData(blob_id))
          total_number_of_chunks += 1
          continue

        if blob_row["bytes"]:
          current_blob_data.extend(blob_row["bytes"])
          total_number_of_chunks += 1

      if current_record is not None:
        yield ChromiumBlobInfo(
            row_id=current_record["row_id"],
            object_type=current_record["object_type"],
            mime_type=current_record["mime_type"],
            size_bytes=current_record["size_bytes"],
            file_name=current_record["file_name"],
            number_of_chunks=total_number_of_chunks,
            blob_data=bytes(current_blob_data),
        )

  def _EnumerateCursor(
      self,
      cursor: sqlite3.Cursor,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
      load_blobs: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields ChromiumIndexedDBRecord records from a sqlite3 cursor.

    Args:
      cursor: the sqlite3 cursor.
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.
      load_blobs: whether to load the record blobs.

    Yields:
      ChromiumIndexedDBRecord records.
    """
    for row in cursor:
      row_id = row[0]
      object_store_id = row[1]
      compression_type = definitions.DatabaseCompressionType(row[2])
      raw_key = row[3]
      raw_value = row[4]
      has_blobs = bool(row[5])

      key, value = None, None
      if parse_key and raw_key:
        key = record.SortableIDBKey.FromBytes(raw_data=raw_key, base_offset=0)

      if parse_value and raw_value:
        if compression_type == definitions.DatabaseCompressionType.UNCOMPRESSED:
          value = blink.V8ScriptValueDecoder.FromBytes(raw_value)
        elif compression_type == definitions.DatabaseCompressionType.ZSTD:
          value = blink.V8ScriptValueDecoder.FromBytes(
              zstd.decompress(raw_value)
          )
        elif compression_type == definitions.DatabaseCompressionType.SNAPPY:
          value = blink.V8ScriptValueDecoder.FromBytes(
              snappy.decompress(raw_value)
          )

      if load_blobs and raw_value is None:
        if not has_blobs:
          raise ValueError("Raw value is None but has_blobs is not set")
        blobs = list(self.LoadBlobDataForRecordId(row_id))
        if len(blobs) == 1:
          value = blobs[0]
        else:
          value = blobs if blobs else None

      yield ChromiumIndexedDBRecord(
          row_id=row_id,
          object_store_id=object_store_id,
          compression_type=compression_type,
          key=key,
          value=value,
          has_blobs=has_blobs,
          raw_key=raw_key if include_raw_data else None,
          raw_value=raw_value if include_raw_data else None,
      )

  def RecordsByObjectStoreId(
      self,
      object_store_id: int,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
      load_blobs: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields ChromiumIndexedDBRecord records for a given object store ID.

    Args:
      object_store_id: the object store ID.
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.
      load_blobs: whether to load the record blobs.

    Yields:
      ChromiumIndexedDBRecord records.
    """
    with sqlite3.connect(self._filename) as conn:
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()
      cursor.execute(definitions.SQL_RECORDS_BY_ID_QUERY, (object_store_id,))
      yield from self._EnumerateCursor(
          cursor, include_raw_data, parse_key, parse_value, load_blobs
      )

  def RecordsByObjectStoreName(
      self,
      object_store_name: str,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
      load_blobs: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields ChromiumIndexedDBRecord records for a given object store name.

    Args:
      object_store_name: the object store name.
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.
      load_blobs: whether to load the record blobs.

    Yields:
      ChromiumIndexedDBRecord records.
    """
    with sqlite3.connect(self._filename) as conn:
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()
      cursor.execute(
          definitions.SQL_RECORDS_BY_NAME_QUERY,
          (object_store_name.encode("utf-16-le"),),
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, parse_key, parse_value, load_blobs
      )

  def Records(
      self,
      include_raw_data: bool = False,
      parse_key: bool = True,
      parse_value: bool = True,
      load_blobs: bool = True,
  ) -> Generator[ChromiumIndexedDBRecord, None, None]:
    """Yields ChromiumIndexedDBRecord records from all object stores.

    Args:
      include_raw_data: whether to include the raw data.
      parse_key: whether to parse the key.
      parse_value: whether to parse the value.
      load_blobs: whether to load the record blobs.

    Yields:
      ChromiumIndexedDBRecord records.
    """
    with sqlite3.connect(self._filename) as conn:
      conn.row_factory = sqlite3.Row
      cursor = conn.cursor()
      cursor.execute(definitions.SQL_RECORDS_QUERY)
      yield from self._EnumerateCursor(
          cursor, include_raw_data, parse_key, parse_value, load_blobs
      )
