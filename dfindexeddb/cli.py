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
"""A CLI tool for dfindexeddb."""
import argparse
import pathlib
import sys
import traceback

from dfindexeddb.leveldb import log
from dfindexeddb.leveldb import ldb
from dfindexeddb import errors
from dfindexeddb.indexeddb import blink
from dfindexeddb.indexeddb import chromium


def IndexeddbCommand(args):
  """The CLI for processing a log/ldb file as indexeddb."""
  if args.source.name.endswith('.log'):
    records = list(
        log.LogFileReader(args.source).GetKeyValueRecords())
  elif args.source.name.endswith('.ldb'):
    records = list(
        ldb.LdbFileReader(args.source).GetKeyValueRecords())
  else:
    print('Unsupported file type.')
    return

  for record in records:
    idbkey = chromium.IndexedDbKey.FromBytes(
        record.key, base_offset=record.offset)

    if record.type == 0:
      print(f'[Deleted LevelDB Key offset={record.offset}]', idbkey)
    else:
      print(f'[LevelDB Key offset={record.offset}]', idbkey)

      value = idbkey.ParseValue(record.value)
      print(f'[LevelDB Value offset={record.offset}]', value)

      if not isinstance(idbkey, chromium.ObjectStoreDataKey):
        continue

      # The ObjectStoreDataKey value should decode as a 2-tuple comprising
      # a version integer and a SSV as a raw byte string
      if not (isinstance(value, tuple) and len(value) == 2 and
          isinstance(value[1], bytes)):
        continue

      try:
        value = blink.V8ScriptValueDecoder.FromBytes(value[1])
        print('[Blink]', value)
      except (errors.ParserError, errors.DecoderError) as err:
        print(f'Error parsing blink value: {err}')
        print(f'Traceback: {traceback.format_exc()}')


def LdbCommand(args):
  """The CLI for processing ldb files."""
  ldb_file = ldb.LdbFileReader(args.source)

  if args.structure_type == 'blocks':
    # Prints block information.
    for block in ldb_file.GetBlocks():
      print(block)

  elif args.structure_type == 'records':
    # Prints key value record information.
    for records in ldb_file.GetKeyValueRecords():
      print(records)


def LogCommand(args):
  """The CLI for processing log files."""
  log_file = log.LogFileReader(args.source)

  if args.structure_type == 'blocks':
    # Prints block information.
    for block in log_file.GetBlocks():
      print(block)

  elif args.structure_type == 'physical_records':
    # Prints log file physical record information.
    for log_file_record in log_file.GetPhysicalRecords():
      print(log_file_record)

  elif args.structure_type == 'write_batches':
    # Prints log file batch information.
    for batch in log_file.GetWriteBatches():
      print(batch)

  elif args.structure_type in ('parsed_internal_key', 'records'):
    # Prints key value record information.
    for records in log_file.GetKeyValueRecords():
      print(records)


def App():
  """The CLI app entrypoint."""
  parser = argparse.ArgumentParser(
      prog='dfindexeddb',
      description='A cli tool for the dfindexeddb package')

  parser.add_argument(
      '-s', '--source', required=True, type=pathlib.Path)

  subparsers = parser.add_subparsers(required=True)

  parser_log = subparsers.add_parser('log')
  parser_log.add_argument(
      'structure_type', choices=[
          'blocks',
          'physical_records',
          'write_batches',
          'parsed_internal_key',
          'records'])
  parser_log.set_defaults(func=LogCommand)

  parser_log = subparsers.add_parser('ldb')
  parser_log.add_argument(
      'structure_type', choices=[
          'blocks',
          'records'])
  parser_log.set_defaults(func=LdbCommand)

  parser_log = subparsers.add_parser('indexeddb')
  parser_log.set_defaults(func=IndexeddbCommand)

  args = parser.parse_args()

  args.func(args)
