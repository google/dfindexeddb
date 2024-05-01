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
from typing import Generator, Optional, Union

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
    level: the leveldb level, None indicates the record came from a log file or
        a file not part of the active file set (determined by a MANIFEST file).
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
  ) -> Generator[LevelDBRecord, None, None]:
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


class FolderReader:
  """A LevelDB folder reader.

  Attributes:
    foldername (str): the source LevelDB folder.
  """

  def __init__(self, foldername: pathlib.Path):
    """Initializes the FolderReader.

    Args:
      foldername: the source LevelDB folder.

    Raises:
      ValueError: if foldername is None or not a directory.
    """
    if not foldername or not foldername.is_dir():
      raise ValueError(f'{foldername} is None or not a directory')
    self.foldername = foldername

  def LogFiles(self) -> Generator[pathlib.Path, None, None]:
    """Returns the log filenames."""
    yield from self.foldername.glob('*.log')

  def LdbFiles(self) -> Generator[pathlib.Path, None, None]:
    """Returns the ldb filenames."""
    yield from self.foldername.glob('*.ldb')

  def Manifest(self) -> Generator[pathlib.Path, None, None]:
    """Returns the Manifest filenames."""
    yield from self.foldername.glob('MANIFEST-*')

  def GetCurrentManifestPath(self) -> pathlib.Path:
    """Returns the path of the current manifest file."""
    current_path = self.foldername / 'CURRENT'
    if not current_path.exists():
      raise errors.ParserError(f'{current_path!s} does not exist.')

    current_manifest = current_path.read_text().strip()
    manifest_regex = re.compile(definitions.MANIFEST_FILENAME_PATTERN)
    if not manifest_regex.fullmatch(current_manifest):
      raise errors.ParserError(
          f'{current_path!s} does not contain the expected content')

    manifest_path = self.foldername / current_manifest
    if not manifest_path.exists():
      raise errors.ParserError(f'{manifest_path!s} does not exist.')
    return manifest_path

  def GetLatestVersion(self) -> descriptor.LevelDBVersion:
    """Returns the latest LevelDBVersion."""
    current_manifest_path = self.GetCurrentManifestPath()
    latest_version = descriptor.FileReader(
        str(current_manifest_path)).GetLatestVersion()
    if not latest_version:
      raise errors.ParserError(
          f'Could not parse a leveldb version from {current_manifest_path!s}')
    return latest_version

  def _GetRecordsByFile(
      self, filename: pathlib.Path) -> Generator[LevelDBRecord, None, None]:
    """Yields the LevelDBRecords from a file.

    Non-log/ldb files are ignored.

    Args:
      filename: the source LevelDB file.

    Yields:
      LevelDBRecords
    """
    if filename.name.endswith('.log'):
      yield from self._GetLogRecords(filename)
    elif filename.name.endswith('.ldb'):
      yield from self._GetLdbRecords(filename)
    elif filename.name.startswith('MANIFEST'):
      print(f'Ignoring descriptor file {filename.as_posix()}', file=sys.stderr)
    elif filename.name in ('LOCK', 'CURRENT', 'LOG', 'LOG.old'):
      print(f'Ignoring {filename.as_posix()}', file=sys.stderr)
    else:
      print(f'Unsupported file type {filename.as_posix()}', file=sys.stderr)

  def _GetLogRecords(
      self,
      filename: pathlib.Path
  ) -> Generator[LevelDBRecord, None, None]:
    """Yields the LevelDBRecords from a log file.

    Args:
      filename: the source LevelDB file.

    Yields:
      LevelDBRecords
    """
    for record in log.FileReader(filename.as_posix()).GetParsedInternalKeys():
      yield LevelDBRecord(path=filename.as_posix(), record=record)

  def _GetLdbRecords(
      self,
      filename: pathlib.Path
  ) -> Generator[LevelDBRecord, None, None]:
    """Yields the LevelDBRecords from a log file.

    Args:
      filename: the source LevelDB file.

    Yields:
      LevelDBRecords
    """
    for record in ldb.FileReader(filename.as_posix()).GetKeyValueRecords():
      yield LevelDBRecord(path=filename.as_posix(), record=record)

  def _RecordsByManifest(self) -> Generator[LevelDBRecord, None, None]:
    """Yields LevelDBRecords using the active files determined by the current
    MANIFEST file.

    Using this method ensures the recovered fields of the
    LevelDBRecord are populated.

    Yields:
      LevelDBRecords.
    """
    latest_version = self.GetLatestVersion()

    processed_files = set()

    # read log records
    log_records = []
    if latest_version.current_log:
      current_log_filename = self.foldername / latest_version.current_log
      if current_log_filename.exists():
        log_records = list(self._GetLogRecords(filename=current_log_filename))
        processed_files.add(current_log_filename)
    else:
      print('No current log file.', file=sys.stderr)

    # read records from the "young" or 0-level
    young_records = []
    for active_file in latest_version.active_files.get(0, {}).keys():
      current_young_filename = self.foldername / active_file
      if current_young_filename.exists():
        young_records = list(self._GetLdbRecords(current_young_filename))
        processed_files.add(current_young_filename)

    # update the recovered attribute based on the sequence number and key.
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
          current_filename = self.foldername / filename
          if current_filename.exists():
            processed_files.add(current_filename)
            for record in self._GetLdbRecords(filename=current_filename):
              record.recovered = record.record.key in active_records
              record.level = level
              yield record
          else:
            print(
                f'Could not find {current_filename} for level {level}.',
                file=sys.stderr)

    # as a final step, parse any other log/ldb files which we treat as orphans
    # since they aren't listed in the active file set.
    for log_file in self.LogFiles():
      if log_file in processed_files:
        continue
      for record in self._GetLogRecords(filename=log_file):
        record.recovered = True
        yield record

    for ldb_file in self.LdbFiles():
      if ldb_file in processed_files:
        continue
      for record in self._GetLdbRecords(filename=ldb_file):
        record.recovered = True
        yield record

  def GetRecords(
      self,
      use_manifest: bool = False
  ) -> Generator[LevelDBRecord, None, None]:
    """Yield LevelDBRecords.

    Args:
      use_manifest: True to use the current manifest in the folder as a means to
          find the active file set.

    Yields:
      LevelDBRecords.
    """
    if use_manifest:
      yield from self._RecordsByManifest()
    else:
      for filename in self.foldername.iterdir():
        yield from LevelDBRecord.FromFile(filename)
