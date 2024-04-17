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
import enum
from datetime import datetime
import json
import pathlib
import sys
import traceback

from dfindexeddb import errors
from dfindexeddb import version
from dfindexeddb.leveldb import record as leveldb_record
from dfindexeddb.indexeddb.chromium import record as chromium_record
from dfindexeddb.indexeddb.chromium import v8


_VALID_PRINTABLE_CHARACTERS = (
    ' abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' +
    '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~.')


class Encoder(json.JSONEncoder):
  """A JSON encoder class for dfindexeddb fields."""
  def default(self, o):
    if dataclasses.is_dataclass(o):
      o_dict = dataclasses.asdict(o)
      return o_dict
    if isinstance(o, bytes):
      out = []
      for x in o:
        if chr(x) not in _VALID_PRINTABLE_CHARACTERS:
          out.append(f'\\x{x:02X}')
        else:
          out.append(chr(x))
      return ''.join(out)
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
    if isinstance(o, enum.Enum):
      return o.name
    return json.JSONEncoder.default(self, o)


def _Output(structure, output):
  """Helper method to output parsed structure to stdout."""
  if output == 'json':
    print(json.dumps(structure, indent=2, cls=Encoder))
  elif output == 'jsonl':
    print(json.dumps(structure, cls=Encoder))
  elif output == 'repr':
    print(structure)


def DbCommand(args):
  """The CLI for processing a directory as indexeddb."""
  if args.use_manifest:
    for db_record in leveldb_record.LevelDBRecord.FromManifest(args.source):
      record = db_record.record
      try:
        idb_record = chromium_record.IndexedDBRecord.FromLevelDBRecord(
            db_record)
      except(
          errors.ParserError,
          errors.DecoderError,
          NotImplementedError) as err:
        print((
            f'Error parsing Indexeddb record {record.__class__.__name__}: {err}'
            f' at offset {record.offset} in {db_record.path}'), file=sys.stderr)
        print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)
        continue
      _Output(idb_record, output=args.output)
  else:
    for db_record in leveldb_record.LevelDBRecord.FromDir(args.source):
      record = db_record.record
      try:
        idb_record = chromium_record.IndexedDBRecord.FromLevelDBRecord(
            db_record)
      except(
          errors.ParserError,
          errors.DecoderError,
          NotImplementedError) as err:
        print((
            f'Error parsing Indexeddb record {record.__class__.__name__}: {err}'
            f' at offset {record.offset} in {db_record.path}'), file=sys.stderr)
        print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)
        continue
      _Output(idb_record, output=args.output)


def LdbCommand(args):
  """The CLI for processing a leveldb table (.ldb) file as indexeddb."""
  for db_record in leveldb_record.LevelDBRecord.FromFile(args.source):
    record = db_record.record
    try:
      idb_record = chromium_record.IndexedDBRecord.FromLevelDBRecord(
          db_record)
    except(
        errors.ParserError,
        errors.DecoderError,
        NotImplementedError) as err:
      print(
          (f'Error parsing Indexeddb record {record.__class__.__name__}: {err} '
           f'at offset {record.offset} in {db_record.path}'), file=sys.stderr)
      print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)
      continue
    _Output(idb_record, output=args.output)


def LogCommand(args):
  """The CLI for processing a leveldb log file as indexeddb."""
  for db_record in leveldb_record.LevelDBRecord.FromFile(args.source):
    record = db_record.record
    try:
      idb_record = chromium_record.IndexedDBRecord.FromLevelDBRecord(
          db_record)
    except(
        errors.ParserError,
        errors.DecoderError,
        NotImplementedError) as err:
      print(
          (f'Error parsing Indexeddb record {record.__class__.__name__}: {err} '
           f'at offset {record.offset} in {db_record.path}'), file=sys.stderr)
      print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)
      continue
    _Output(idb_record, output=args.output)


def App():
  """The CLI app entrypoint for dfindexeddb."""
  parser = argparse.ArgumentParser(
      prog='dfindexeddb',
      description='A cli tool for parsing indexeddb files',
      epilog=f'Version {version.GetVersion()}')

  subparsers = parser.add_subparsers()

  parser_db = subparsers.add_parser(
      'db', help='Parse a directory as indexeddb.')
  parser_db.add_argument(
      '-s', '--source', required=True, type=pathlib.Path,
      help='The source leveldb folder')
  parser_db.add_argument(
      '--use_manifest',
      action='store_true',
      help='Use manifest file to determine active/deleted records.')
  parser_db.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  parser_db.set_defaults(func=DbCommand)

  parser_ldb = subparsers.add_parser(
      'ldb', help='Parse a ldb file as indexeddb.')
  parser_ldb.add_argument(
      '-s', '--source', required=True, type=pathlib.Path,
      help='The source .ldb file.')
  parser_ldb.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  parser_ldb.set_defaults(func=LdbCommand)

  parser_log = subparsers.add_parser(
      'log', help='Parse a log file as indexeddb.')
  parser_log.add_argument(
      '-s', '--source', required=True, type=pathlib.Path,
      help='The source .log file.')
  parser_log.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  parser_log.set_defaults(func=LogCommand)

  args = parser.parse_args()
  args.func(args)
