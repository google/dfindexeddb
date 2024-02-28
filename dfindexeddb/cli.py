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
import dataclasses
from datetime import datetime
import json
import pathlib
import sys

from dfindexeddb.leveldb import log
from dfindexeddb.leveldb import ldb
from dfindexeddb.indexeddb import chromium
from dfindexeddb.indexeddb import v8


class Encoder(json.JSONEncoder):
  """A JSON encoder class for dfindexeddb fields."""
  def default(self, o):
    if isinstance(o, bytes):
      return o.decode(encoding='ascii', errors='backslashreplace')
    if isinstance(o, datetime):
      return o.isoformat()
    if isinstance(o, v8.Undefined):
      return "<undefined>"
    if isinstance(o, v8.Null):
      return "<null>"
    if isinstance(o, set):
      return list(o)
    if isinstance(o, v8.RegExp):
      return str(o)
    return json.JSONEncoder.default(self, o)


def _Output(structure, to_json=False):
  """Helper method to output parsed structure to stdout."""
  if to_json:
    structure_dict = dataclasses.asdict(structure)
    print(json.dumps(structure_dict, indent=2, cls=Encoder))
  else:
    print(structure)


def IndexeddbCommand(args):
  """The CLI for processing a log/ldb file as indexeddb."""
  if args.source.name.endswith('.log'):
    records = list(
        log.LogFileReader(args.source).GetKeyValueRecords())
  elif args.source.name.endswith('.ldb'):
    records = list(
        ldb.LdbFileReader(args.source).GetKeyValueRecords())
  else:
    print('Unsupported file type.', file=sys.stderr)
    return

  for record in records:
    record = chromium.IndexedDBRecord.FromLevelDBRecord(record)
    _Output(record, to_json=args.json)


def LdbCommand(args):
  """The CLI for processing ldb files."""
  ldb_file = ldb.LdbFileReader(args.source)

  if args.structure_type == 'blocks':
    # Prints block information.
    for block in ldb_file.GetBlocks():
      _Output(block, to_json=args.json)

  elif args.structure_type == 'records':
    # Prints key value record information.
    for record in ldb_file.GetKeyValueRecords():
      _Output(record, to_json=args.json)


def LogCommand(args):
  """The CLI for processing log files."""
  log_file = log.LogFileReader(args.source)

  if args.structure_type == 'blocks':
    # Prints block information.
    for block in log_file.GetBlocks():
      _Output(block, to_json=args.json)

  elif args.structure_type == 'physical_records':
    # Prints log file physical record information.
    for log_file_record in log_file.GetPhysicalRecords():
      _Output(log_file_record, to_json=args.json)

  elif args.structure_type == 'write_batches':
    # Prints log file batch information.
    for batch in log_file.GetWriteBatches():
      _Output(batch, to_json=args.json)

  elif args.structure_type in ('parsed_internal_key', 'records'):
    # Prints key value record information.
    for record in log_file.GetKeyValueRecords():
      _Output(record, to_json=args.json)


def App():
  """The CLI app entrypoint."""
  parser = argparse.ArgumentParser(
      prog='dfindexeddb',
      description='A cli tool for the dfindexeddb package')

  parser.add_argument(
      '-s', '--source', required=True, type=pathlib.Path, 
      help='The source leveldb file')
  parser.add_argument('--json', action='store_true', help='Output as JSON')
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
