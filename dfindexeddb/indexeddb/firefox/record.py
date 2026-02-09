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
"""Firefox IndexedDB records."""
import pathlib
import sqlite3
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Generator, List, Optional

from dfindexeddb import errors
from dfindexeddb.indexeddb.firefox import gecko


@dataclass
class FirefoxBlobInfo:
  """Firefox IndexedDB blob info.

  Attributes:
    file_id: the file identifier.
    file_path: the full path to the blob file.
    blob_data: the blob data.
  """

  file_id: str
  file_path: str
  blob_data: Any = None


@dataclass
class FirefoxObjectStoreInfo:
  """A FireFox ObjectStoreInfo.

  Attributes:
    id: the object store ID.
    name: the object store name.
    key_path: the object store key path.
    auto_inc: the current auto-increment value.
      database_name: the database name from the database table.
  """

  id: int
  name: str
  key_path: str
  auto_inc: int
  database_name: str


@dataclass
class FirefoxIndexedDBRecord:
  """A Firefox IndexedDBRecord.

  Attributes:
    key: the parsed key.
    value: the parsed value.
    file_ids: the file identifiers.
    object_store_id: the object store id.
    object_store_name: the object store name from the object_store table.
    database_name: the IndexedDB database name from the database table.
    raw_key: the raw key.
    raw_value: the raw value.
  """

  key: Any
  value: Any
  file_ids: Optional[str]
  object_store_id: int
  object_store_name: str
  database_name: str
  raw_key: Optional[bytes] = None
  raw_value: Optional[bytes] = None
  blobs: Optional[List[FirefoxBlobInfo]] = None


class FileReader:
  """A reader for Firefox IndexedDB sqlite3 files.

  Attributes:
    database_name: the database name.
    origin: the database origin.
    metadata_version: the metadata version.
    last_vacuum_time: the last vacuum time.
    last_analyze_time: the last analyze time.
  """

  def __init__(self, filename: str):
    """Initializes the FileReader.

    Args:
      filename: the IndexedDB filename.
    """
    self.filename = filename
    self._uri = pathlib.Path(filename).resolve().as_uri()

    with sqlite3.connect(f"{self._uri}?mode=ro", uri=True) as conn:
      cursor = conn.execute(
          "SELECT name, origin, version, last_vacuum_time, last_analyze_time "
          "FROM database"
      )
      result = cursor.fetchone()
      self.database_name = result[0]
      self.origin = result[1]
      self.metadata_version = result[2]
      self.last_vacuum_time = result[3]
      self.last_analyze_time = result[4]

  def _ParseKey(self, key: bytes) -> Any:
    """Parses a key."""
    try:
      return gecko.IDBKey.FromBytes(key)
    except errors.ParserError as e:
      print("failed to parse", key, file=sys.stderr)
      traceback.print_exception(type(e), e, e.__traceback__)
      return key

  def _ParseValue(self, value: bytes) -> Any:
    """Parses a value."""
    try:
      return gecko.JSStructuredCloneDecoder.FromBytes(value)
    except errors.ParserError as err:
      print("failed to parse", value, file=sys.stderr)
      traceback.print_exception(type(err), err, err.__traceback__)
      return value

  def LoadBlobsForRecord(
      self, file_ids: Optional[str] = None
  ) -> List[FirefoxBlobInfo]:
    """Returns the FirefoxBlobInfo instances for the given file_ids string.

    Args:
      file_ids: the file identifiers (e.g. ".2" or "1 2 3").

    Returns:
      a list of FirefoxBlobInfo instances.
    """
    blobs: list[FirefoxBlobInfo] = []
    if not file_ids:
      return blobs

    ids = file_ids.strip(".").split(" ")
    for file_id in ids:
      if not file_id:
        continue
      file_name = str(abs(int(file_id)))  # mutable file ids are -ve?
      blob_file_path = (
          pathlib.Path(self.filename).with_suffix(".files") / file_name
      )
      blob_data = None
      if blob_file_path.exists():
        blob_data = blob_file_path.read_bytes()
        try:
          blob_data = gecko.JSStructuredCloneDecoder.FromBytes(blob_data)
        except errors.ParserError as err:
          print(
              f"Failed to parse blob {file_id}, defaulting to raw value as it "
              f"is unlikely to be a JS value: {err}",
              file=sys.stderr,
          )

      blobs.append(
          FirefoxBlobInfo(
              file_id=file_id,
              file_path=str(blob_file_path),
              blob_data=blob_data,
          )
      )
    return blobs

  def ObjectStores(self) -> Generator[FirefoxObjectStoreInfo, None, None]:
    """Returns the Object Store information from the IndexedDB database.

    Yields:
      FirefoxObjectStoreInfo instances.
    """
    with sqlite3.connect(f"{self._uri}?mode=ro", uri=True) as conn:
      cursor = conn.execute(
          "SELECT id, auto_increment, name, key_path FROM object_store"
      )
      results = cursor.fetchall()
      for result in results:
        yield FirefoxObjectStoreInfo(
            id=result[0],
            name=result[2],
            key_path=result[3],
            auto_inc=result[1],
            database_name=self.database_name,
        )

  def _EnumerateCursor(
      self,
      cursor: sqlite3.Cursor,
      include_raw_data: bool = False,
      load_blobs: bool = True,
  ) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Yields FirefoxIndexedDBRecord records from a sqlite3 cursor.

    Args:
      cursor: the sqlite3 cursor.
      include_raw_data: whether to include the raw data.
      load_blobs: whether to load the record blobs.

    Yields:
      FirefoxIndexedDBRecord records.
    """
    for row in cursor:
      key = self._ParseKey(row[0])
      file_ids = row[3]
      if isinstance(file_ids, bytes):
        file_ids = file_ids.decode("utf-8")

      if isinstance(row[1], bytes):
        value = self._ParseValue(row[1])
      else:
        value = row[1]

      blobs = None
      if load_blobs and file_ids:
        blobs = self.LoadBlobsForRecord(file_ids)

      yield FirefoxIndexedDBRecord(
          key=key,
          value=value,
          object_store_id=row[2],
          file_ids=file_ids,
          object_store_name=row[4].decode("utf-8"),
          database_name=self.database_name,
          raw_key=row[0] if include_raw_data else None,
          raw_value=row[1] if include_raw_data else None,
          blobs=blobs,
      )

  def RecordsByObjectStoreId(
      self,
      object_store_id: int,
      include_raw_data: bool = False,
      load_blobs: bool = True,
  ) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Returns FirefoxIndexedDBRecords by a given object store id.

    Args:
      object_store_id: the object store id.
      include_raw_data: whether to include the raw data.
      load_blobs: whether to load the record blobs.
    """
    with sqlite3.connect(f"{self._uri}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT od.key, od.data, od.object_store_id, od.file_ids, os.name "
          "FROM object_data od "
          "JOIN object_store os ON od.object_store_id == os.id "
          "WHERE os.id = ? ORDER BY od.key",
          (object_store_id,),
      )
      yield from self._EnumerateCursor(cursor, include_raw_data, load_blobs)

  def Records(
      self, include_raw_data: bool = False, load_blobs: bool = True
  ) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Returns FirefoxIndexedDBRecords from the database

    Args:
      include_raw_data: whether to include the raw data.
      load_blobs: whether to load the record blobs.

    Yields:
      FirefoxIndexedDBRecord instances.
    """
    with sqlite3.connect(f"{self._uri}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT od.key, od.data, od.object_store_id, od.file_ids, os.name "
          "FROM object_data od "
          "JOIN object_store os ON od.object_store_id == os.id"
      )
      yield from self._EnumerateCursor(cursor, include_raw_data, load_blobs)


class FolderReader:
  """A reader for a FireFox IndexedDB folder.

  The path takes a general form of ./<origin>/idb/<filename>.[files|sqlite]

  """

  def __init__(self, folder_name: pathlib.Path):
    """Initializes the FireFox IndexedDB FolderReader.

    Args:
      folder_name: the IndexedDB folder name (the origin folder).

    Raises:
      ValueError: if the folder does not exist or is not a directory.
    """
    self.folder_name = folder_name
    if not self.folder_name.exists():
      raise ValueError(f"{folder_name} does not exist.")
    if not self.folder_name.is_dir():
      raise ValueError(f"{folder_name} is not a directory.")

    self.file_names: list[pathlib.Path] = []
    for file_name in self.folder_name.rglob("idb/*.sqlite"):
      self.file_names.append(file_name)

  def Records(
      self, include_raw_data: bool = False, load_blobs: bool = True
  ) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Returns FirefoxIndexedDBRecords from the IndexedDB folder."""
    for file_name in self.file_names:
      yield from FileReader(str(file_name)).Records(
          include_raw_data=include_raw_data, load_blobs=load_blobs
      )
