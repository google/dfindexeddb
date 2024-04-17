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
"""A module for records from LevelDB files."""
from __future__ import annotations
import dataclasses
import pathlib
import re
import sys
from typing import Any, Generator, Optional, Union

from dfindexeddb import errors
from dfindexeddb.leveldb import definitions
from dfindexeddb.leveldb import descriptor
from dfindexeddb.leveldb import ldb
from dfindexeddb.leveldb import log


@dataclasses.dataclass
class LevelDBRecord:
  """A leveldb record.

  A record can come from a log file, a table (ldb) file or a descriptor
  (MANIFEST) file.

  Attributes:
    path: the file path where the record was parsed from.
    record: the leveldb record.
    level: the leveldb level, None indicates the record came from a log file.
    recovered: True if the record is a recovered record.
  """
  path: str
  record: Union[
      ldb.KeyValueRecord,
      log.ParsedInternalKey]
  level: Optional[int] = None
  recovered: Optional[bool] = None

  @classmethod
  def FromFile(
      cls,
      file_path: pathlib.Path
  ) -> Generator[LevelDBRecord, Any, Any]:
    """Yields leveldb records from the given path.

    Yields:
      LevelDBRecords

    Args:
      file_path: the file path.
    """
    if file_path.name.endswith('.log'):
      for record in log.FileReader(
          file_path.as_posix()).GetParsedInternalKeys():
        yield cls(path=file_path.as_posix(), record=record)
    elif file_path.name.endswith('.ldb'):
      for record in ldb.FileReader(file_path.as_posix()).GetKeyValueRecords():
        yield cls(path=file_path.as_posix(), record=record)
    elif file_path.name.startswith('MANIFEST'):
      print(f'Ignoring descriptor file {file_path.as_posix()}', file=sys.stderr)
    elif file_path.name in ('LOCK', 'CURRENT', 'LOG', 'LOG.old'):
      print(f'Ignoring {file_path.as_posix()}', file=sys.stderr)
    else:
      print(f'Unsupported file type {file_path.as_posix()}', file=sys.stderr)

  @classmethod
  def FromDir(
      cls,
      path: pathlib.Path
  ) -> Generator[LevelDBRecord, Any, Any]:
    """Yields LevelDBRecords from the given directory.

    Args:
      path: the file path.

    Yields:
      LevelDBRecords
    """
    if not path or not path.is_dir():
      raise ValueError(f'{path} is not a directory')
    for file_path in path.iterdir():
      yield from cls.FromFile(file_path=file_path)

  @classmethod
  def FromManifest(
      cls,
      path: pathlib.Path
  ) -> Generator[LevelDBRecord, Any, Any]:
    """Yields LevelDBRecords from the given directory using the manifest.

    Args:
      path: the file path.

    Yields:
      LevelDBRecords

    Raises:
      ParserError: if the CURRENT or MANIFEST-* file does not exist.
      ValueError: if path is not a directory.
    """
    if not path or not path.is_dir():
      raise ValueError(f'{path} is not a directory')

    current_path = path / 'CURRENT'
    if not current_path.exists():
      raise errors.ParserError(f'{current_path!s} does not exist.')

    current_manifest = current_path.read_text().strip()
    manifest_regex = re.compile(definitions.MANIFEST_FILENAME_PATTERN)
    if not manifest_regex.fullmatch(current_manifest):
      raise errors.ParserError(
          f'{current_path!s} does not contain the expected content')

    manifest_path = path / current_manifest
    if not manifest_path.exists():
      raise errors.ParserError(f'{manifest_path!s} does not exist.')

    latest_version = descriptor.FileReader(
        str(manifest_path)).GetLatestVersion()
    if not latest_version:
      raise errors.ParserError(
          f'Could not parse a leveldb version from {manifest_path!s}')

    # read log records
    log_records = []
    if latest_version.current_log:
      current_log = path / latest_version.current_log
      if current_log.exists():
        for log_record in cls.FromFile(file_path=current_log):
          log_records.append(log_record)
    else:
      print('No current log file.', file=sys.stderr)

    # read records from the "young" or 0-level
    young_records = []
    for active_file in latest_version.active_files.get(0, {}).keys():
      current_young = path / active_file
      if current_young.exists():
        for young_record in cls.FromFile(current_young):
          young_records.append(young_record)

    active_records = {}
    for record in sorted(
        log_records,
        key=lambda record: record.record.sequence_number,
        reverse=True):
      if record.record.key not in active_records:
        record.recovered = False
        active_records[record.record.key] = record
      else:
        record.recovered = True

    for record in sorted(
        young_records,
        key=lambda record: record.record.sequence_number,
        reverse=True):
      if record.record.key not in active_records:
        record.recovered = False
        active_records[record.record.key] = record
      else:
        record.recovered = True
      record.level = 0

    yield from sorted(
        log_records + young_records,
        key=lambda record: record.record.sequence_number,
        reverse=False)

    if latest_version.active_files.keys():
      for level in range(1, max(latest_version.active_files.keys()) + 1):
        for filename in latest_version.active_files.get(level, []):
          current_filename = path / filename
          for record in cls.FromFile(file_path=current_filename):
            if record.record.key in active_records:
              record.recovered = True
            else:
              record.recovered = False
            record.level = level
            yield record
