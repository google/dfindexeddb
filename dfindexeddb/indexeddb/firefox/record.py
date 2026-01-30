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
from typing import Any, Generator, Optional

from dfindexeddb import errors
from dfindexeddb.indexeddb.firefox import gecko


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
  """

  key: Any
  value: Any
  file_ids: Optional[str]
  object_store_id: int
  object_store_name: str
  database_name: str
  raw_key: Optional[bytes] = None
  raw_value: Optional[bytes] = None


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

    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
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

  def ObjectStores(self) -> Generator[FirefoxObjectStoreInfo, None, None]:
    """Returns the Object Store information from the IndexedDB database.

    Yields:
      FirefoxObjectStoreInfo instances.
    """
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
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

  def RecordsByObjectStoreId(
      self, object_store_id: int, include_raw_data: bool = False
  ) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Returns FirefoxIndexedDBRecords by a given object store id.

    Args:
      object_store_id: the object store id.
    """
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT od.key, od.data, od.object_store_id, od.file_ids, os.name "
          "FROM object_data od "
          "JOIN object_store os ON od.object_store_id == os.id "
          "WHERE os.id = ? ORDER BY od.key",
          (object_store_id,),
      )
      for row in cursor:
        key = self._ParseKey(row[0])
        if row[3]:
          value = row[1]
        else:
          value = self._ParseValue(row[1])
        yield FirefoxIndexedDBRecord(
            key=key,
            value=value,
            object_store_id=row[2],
            file_ids=row[3],
            object_store_name=row[4].decode("utf-8"),
            database_name=self.database_name,
            raw_key=row[0] if include_raw_data else None,
            raw_value=row[1] if include_raw_data else None,
        )

  def Records(
      self, include_raw_data: bool = False
  ) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Returns FirefoxIndexedDBRecords from the database."""
    with sqlite3.connect(f"file:{self.filename}?mode=ro", uri=True) as conn:
      conn.text_factory = bytes
      cursor = conn.execute(
          "SELECT od.key, od.data, od.object_store_id, od.file_ids, os.name "
          "FROM object_data od "
          "JOIN object_store os ON od.object_store_id == os.id"
      )
      for row in cursor:
        key = self._ParseKey(row[0])
        if row[3]:
          value = row[1]
        else:
          value = self._ParseValue(row[1])
        yield FirefoxIndexedDBRecord(
            key=key,
            value=value,
            object_store_id=row[2],
            file_ids=row[3],
            object_store_name=row[4].decode("utf-8"),
            database_name=self.database_name,
            raw_key=row[0] if include_raw_data else None,
            raw_value=row[1] if include_raw_data else None,
        )


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

  def Records(self) -> Generator[FirefoxIndexedDBRecord, None, None]:
    """Returns FirefoxIndexedDBRecords from the IndexedDB folder."""
    for file_name in self.file_names:
      yield from FileReader(str(file_name)).Records()
