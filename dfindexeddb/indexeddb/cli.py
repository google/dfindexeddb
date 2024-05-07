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

from dfindexeddb import version
from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.indexeddb.chromium import record as chromium_record
from dfindexeddb.indexeddb.chromium import v8
from dfindexeddb.indexeddb.safari import record as safari_record


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


def BlinkCommand(args):
  """The CLI for processing a file as a blink value."""
  with open(args.source, 'rb') as fd:
    buffer = fd.read()
    blink_value = blink.V8ScriptValueDecoder.FromBytes(buffer)
    _Output(blink_value, output=args.output)


def DbCommand(args):
  """The CLI for processing a directory as IndexedDB."""
  if args.format in ('chrome', 'chromium'):
    for db_record in chromium_record.FolderReader(
        args.source).GetRecords(use_manifest=args.use_manifest):
      _Output(db_record, output=args.output)
  elif args.format == 'safari':
    for db_record in safari_record.FileReader(args.source).Records():
      _Output(db_record, output=args.output)


def LdbCommand(args):
  """The CLI for processing a LevelDB table (.ldb) file as IndexedDB."""
  for db_record in chromium_record.IndexedDBRecord.FromFile(args.source):
    _Output(db_record, output=args.output)


def LogCommand(args):
  """The CLI for processing a LevelDB log file as IndexedDB."""
  for db_record in chromium_record.IndexedDBRecord.FromFile(args.source):
    _Output(db_record, output=args.output)


def App():
  """The CLI app entrypoint for dfindexeddb."""
  parser = argparse.ArgumentParser(
      prog='dfindexeddb',
      description='A cli tool for parsing IndexedDB files',
      epilog=f'Version {version.GetVersion()}')

  subparsers = parser.add_subparsers()

  parser_blink = subparsers.add_parser(
      'blink', help='Parse a file as a blink value.')
  parser_blink.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
      help=(
        'The source file.'))
  parser_blink.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  parser_blink.set_defaults(func=BlinkCommand)

  parser_db = subparsers.add_parser(
      'db', help='Parse a directory as IndexedDB.')
  parser_db.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
      help=(
        'The source IndexedDB folder (for chrome/chromium) '
        'or file (for safari).'))
  parser_db.add_argument(
      '--format',
      required=True,
      choices=['chromium', 'chrome', 'safari'],
      help='The type of IndexedDB to parse.')
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
      'ldb',
      help='Parse a ldb file as IndexedDB.')
  parser_ldb.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
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
      'log',
      help='Parse a log file as IndexedDB.')
  parser_log.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
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
  if hasattr(args, 'func'):
    args.func(args)
  else:
    parser.print_help()
