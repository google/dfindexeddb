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
"""A class to represent records from LevelDB files."""
from __future__ import annotations
import dataclasses
import pathlib
import sys
from typing import Any, Generator, Union

from dfindexeddb.leveldb import descriptor
from dfindexeddb.leveldb import ldb
from dfindexeddb.leveldb import log


@dataclasses.dataclass
class LevelDBRecord:
  """A leveldb record.

  A record can come from a log file, a table (ldb) file or a descriptor
  (manifest) file.

  Attributes:
    path: the file path where the record was parsed from.
    record: the leveldb record.
  """
  path: str
  record: Union[
      ldb.KeyValueRecord | log.ParsedInternalKey | descriptor.VersionEdit]

  @classmethod
  def FromFile(
      cls,
      file_path: pathlib.Path,
      include_versionedit: bool = False
  ) -> Generator[LevelDBRecord, Any, Any]:
    """Yields leveldb records from the given path.

    Yields:
      LevelDBRecords

    Args:
      file_path: the file path.
      include_versionedit: include VersionEdit records from descriptor files.
    """
    if file_path.name.endswith('.log'):
      for record in log.FileReader(file_path).GetParsedInternalKeys():
        yield cls(path=file_path.as_posix(), record=record)
    elif file_path.name.endswith('.ldb'):
      for record in ldb.FileReader(file_path).GetKeyValueRecords():
        yield cls(path=file_path.as_posix(), record=record)
    elif file_path.name.startswith('MANIFEST') and include_versionedit:
      for record in descriptor.FileReader(file_path).GetVersionEdits():
        yield cls(path=file_path.as_posix(), record=record)
    elif file_path.name in ('LOCK', 'CURRENT', 'LOG', 'LOG.old'):
      print(f'Ignoring {file_path.as_posix()}', file=sys.stderr)
    else:
      print(f'Unsupported file type {file_path.as_posix()}', file=sys.stderr)

  @classmethod
  def FromDir(
      cls,
      path: pathlib.Path,
      include_versionedit: bool = False
  ) -> Generator[LevelDBRecord, Any, Any]:
    """Yields LevelDBRecords from the given directory.

    Args:
      path: the file path.
      include_versionedit: include VersionEdit records from descriptor files.

    Yields:
      LevelDBRecords

    Raises:
      ValueError: if path is not a directory.
    """
    if path.is_dir():
      for file_path in path.iterdir():
        yield from cls.FromFile(
            file_path=file_path,
            include_versionedit=include_versionedit)
    else:
      raise ValueError(f'{path} is not a directory')
