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
import contextlib
import pathlib
import plistlib
import sqlite3
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Tuple

from dfindexeddb import errors
from dfindexeddb.indexeddb.safari import webkit


@dataclass
class SafariBlobInfo:
  """Safari IndexedDB blob info.

  Attributes:
    blob_url: the blob URL.
    file_name: the file name.
    file_path: the full path to the blob file.
    blob_data: the blob data.
  """

  blob_url: str
  file_name: str
  file_path: str
  blob_data: Optional[bytes] = None


@dataclass
class SafariObjectStoreInfo:
  """A Safari ObjectStoreInfo.

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
class SafariIndexedDBRecord:
  """A Safari IndexedDBRecord.

  Attributes:
    key: the parsed key.
    value: the parsed value.
    object_store_id: the object store id.
    object_store_name: the object store name from the ObjectStoreInfo table.
    database_name: the IndexedDB database name from the IDBDatabaseInfo table.
    record_id: the record ID from the Record table.
    raw_key: the raw key.
    raw_value: the raw value.
  """

  key: Any
  value: Any
  object_store_id: int
  object_store_name: str
  database_name: str
  record_id: int
  raw_key: Optional[bytes] = None
  raw_value: Optional[bytes] = None
  blobs: Optional[List[SafariBlobInfo]] = None

  @property
  def is_key_filterable(self) -> bool:
    """True if the record key is filterable."""
    return True

  @property
  def is_value_filterable(self) -> bool:
    """True if the record value is filterable."""
    return True

  def MatchesKey(self, term: str) -> bool:
    """Returns True if the record key matches the filter term.

    Args:
      term: the filter term.
    """
    key_val = getattr(self.key, "value", self.key)
    return term in str(key_val)

  def MatchesValue(self, term: str) -> bool:
    """Returns True if the record value or blobs matches the filter term.

    Args:
      term: the filter term.
    """
    if term in str(self.value):
      return True

    if self.blobs:
      for blob_info in self.blobs:
        if blob_info.blob_data is not None and term in str(blob_info.blob_data):
          return True
    return False


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
    self._uri = pathlib.Path(filename).resolve().as_uri()
    self.database_name = ""
    self.database_version = 0
    self.metadata_version = 0
    self.max_object_store_id = 0

    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "DatabaseVersion"'
      )
      result = cursor.fetchone()
      if result:
        self.database_version = int(self._DecodeString(result[0]))

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "MetadataVersion"'
      )
      result = cursor.fetchone()
      if result:
        self.metadata_version = int(self._DecodeString(result[0]))

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "DatabaseName"'
      )
      result = cursor.fetchone()
      if result:
        self.database_name = self._DecodeString(result[0])

      cursor = conn.execute(
          'SELECT value FROM IDBDatabaseInfo WHERE key = "MaxObjectStoreID"'
      )
      result = cursor.fetchone()
      if result:
        self.max_object_store_id = int(self._DecodeString(result[0]))

  def _DecodeString(self, data: Any, vtype: Optional[str] = None) -> str:
    """Decodes a string from Safari IndexedDB metadata.

    Safari metadata strings are stored in SQLite as either:
    1. UTF-8 TEXT (returned as str or with vtype='text')
    2. UTF-16-LE BLOB (returned as bytes or with vtype='blob')

    Args:
      data: the string or bytes to decode.
      vtype: optional SQLite type ('text' or 'blob'). If not provided,
          isinstance checks are used.

    Returns:
      the decoded string.
    """
    if not data:
      return ""
    if isinstance(data, str):
      return data

    if isinstance(data, bytes):
      if vtype == "blob" or vtype is None:
        try:
          return data.decode("utf-16-le")
        except UnicodeDecodeError:
          pass
      return data.decode("utf-8", errors="replace")

    return str(data)

  def _CreateBlobInfo(
      self, blob_url_raw: Any, file_name_raw: Any
  ) -> SafariBlobInfo:
    """Decodes, resolves, and loads a SafariBlobInfo instance.

    Args:
      blob_url_raw: the raw blob URL string or bytes.
      file_name_raw: the raw file name string or bytes.

    Returns:
      a SafariBlobInfo instance.
    """
    blob_url = self._DecodeString(blob_url_raw, vtype="text")
    file_name = self._DecodeString(file_name_raw, vtype="text")

    # Check in .blobs subfolder first, then try the base directory
    blob_file_path = pathlib.Path(f"{self.filename}.blobs") / file_name
    if not blob_file_path.exists():
      blob_file_path = pathlib.Path(self.filename).parent / file_name

    blob_data = blob_file_path.read_bytes() if blob_file_path.exists() else None
    return SafariBlobInfo(
        blob_url=blob_url,
        file_name=file_name,
        file_path=str(blob_file_path),
        blob_data=blob_data,
    )

  def _GetBlobsMap(
      self, conn: sqlite3.Connection, record_id: Optional[int] = None
  ) -> Dict[int, List[SafariBlobInfo]]:
    """Returns a mapping of record IDs to lists of SafariBlobInfo instances.

    Args:
      conn: the sqlite3 connection.
      record_id: optional record ID to filter by.

    Returns:
      a dictionary mapping record ID to a list of SafariBlobInfo instances.
    """
    blobs_map: Dict[int, List[SafariBlobInfo]] = {}
    query = (
        "SELECT r.objectStoreRow, r.blobURL, f.fileName "
        "FROM BlobRecords r "
        "JOIN BlobFiles f ON r.blobURL = f.blobURL"
    )
    params: Tuple[Any, ...] = ()
    if record_id is not None:
      query += " WHERE r.objectStoreRow = ?"
      params = (record_id,)

    cursor = conn.execute(query, params)
    for row in cursor:
      blobs_map.setdefault(row[0], []).append(
          self._CreateBlobInfo(row[1], row[2])
      )
    return blobs_map

  def _LoadBlobs(
      self, record_id: int, conn: sqlite3.Connection
  ) -> List[SafariBlobInfo]:
    """Loads blob info for a given record ID using an active connection.

    Args:
      record_id: the record ID.
      conn: the sqlite3 connection.

    Returns:
      a list of SafariBlobInfo instances.
    """
    return self._GetBlobsMap(conn, record_id=record_id).get(record_id, [])

  def LoadBlobsForRecordId(self, record_id: int) -> List[SafariBlobInfo]:
    """Returns the SafariBlobInfo instances for the given record_id.

    Args:
      record_id: the record ID.

    Returns:
      a list of SafariBlobInfo instances.
    """
    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      return self._LoadBlobs(record_id, conn)

  def ObjectStores(self) -> Generator[SafariObjectStoreInfo, None, None]:
    """Returns the Object Store information from the IndexedDB database.

    Yields:
      ObjectStoreInfo instances.
    """
    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      cursor = conn.execute(
          "SELECT id, name, keypath, autoinc FROM ObjectStoreInfo"
      )
      results = cursor.fetchall()
      for result in results:
        key_path = plistlib.loads(result[2])
        yield SafariObjectStoreInfo(
            id=result[0],
            name=self._DecodeString(result[1]),
            key_path=key_path,
            auto_inc=result[3],
            database_name=self.database_name,
        )

  def _EnumerateCursor(
      self,
      cursor: sqlite3.Cursor,
      include_raw_data: bool = False,
      load_blobs: bool = True,
      blobs_map: Optional[Dict[int, List[SafariBlobInfo]]] = None,
  ) -> Generator[SafariIndexedDBRecord, None, None]:
    """Yields SafariIndexedDBRecord records from a sqlite3 cursor.

    Args:
      cursor: the sqlite3 cursor.
      include_raw_data: whether to include the raw data.
      load_blobs: whether to load the record blobs.
      blobs_map: optional mapping of record IDs to lists of SafariBlobInfo.

    Yields:
      SafariIndexedDBRecord records.
    """
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
      blobs = None
      if load_blobs:
        if blobs_map is not None:
          blobs = blobs_map.get(row[5], [])
        else:
          blobs = self._LoadBlobs(row[5], cursor.connection)
      yield SafariIndexedDBRecord(
          key=key,
          value=value,
          object_store_id=row[2],
          object_store_name=self._DecodeString(row[3], vtype=row[4]),
          database_name=self.database_name,
          record_id=row[5],
          raw_key=row[0] if include_raw_data else None,
          raw_value=row[1] if include_raw_data else None,
          blobs=blobs,
      )

  def RecordById(
      self,
      record_id: int,
      include_raw_data: bool = False,
      load_blobs: bool = True,
  ) -> Optional[SafariIndexedDBRecord]:
    """Returns an IndexedDBRecord for the given record_id.

    Returns:
      the IndexedDBRecord or None if the record_id does not exist in the
          database.
    """
    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, typeof(o.name), "
          "r.recordID FROM "
          "Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id "
          "WHERE r.recordID = ?",
          (record_id,),
      )
      try:
        return next(self._EnumerateCursor(cursor, include_raw_data, load_blobs))
      except StopIteration:
        return None

  def RecordsByObjectStoreName(
      self,
      name: str,
      include_raw_data: bool = False,
      load_blobs: bool = True,
  ) -> Generator[SafariIndexedDBRecord, None, None]:
    """Returns IndexedDBRecords for the given ObjectStore name.

    Yields:
      IndexedDBRecord instances.
    """
    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      blobs_map = self._GetBlobsMap(conn) if load_blobs else None
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, typeof(o.name), "
          "r.recordID FROM "
          "Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id "
          "WHERE o.name = ?",
          (name,),
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, load_blobs, blobs_map=blobs_map
      )

  def RecordsByObjectStoreId(
      self,
      object_store_id: int,
      include_raw_data: bool = False,
      load_blobs: bool = True,
  ) -> Generator[SafariIndexedDBRecord, None, None]:
    """Returns IndexedDBRecords for the given ObjectStore id.

    Yields:
      IndexedDBRecord instances.
    """
    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      blobs_map = self._GetBlobsMap(conn) if load_blobs else None
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, typeof(o.name), "
          "r.recordID "
          "FROM Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id "
          "WHERE o.id = ?",
          (object_store_id,),
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, load_blobs, blobs_map=blobs_map
      )

  def Records(
      self, include_raw_data: bool = False, load_blobs: bool = True
  ) -> Generator[SafariIndexedDBRecord, None, None]:
    """Returns all the IndexedDBRecords."""
    with contextlib.closing(
        sqlite3.connect(f"{self._uri}?mode=ro", uri=True)
    ) as conn:
      blobs_map = self._GetBlobsMap(conn) if load_blobs else None
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT r.key, r.value, r.objectStoreID, o.name, typeof(o.name), "
          "r.recordID "
          "FROM Records r "
          "JOIN ObjectStoreInfo o ON r.objectStoreID == o.id"
      )
      yield from self._EnumerateCursor(
          cursor, include_raw_data, load_blobs, blobs_map=blobs_map
      )
