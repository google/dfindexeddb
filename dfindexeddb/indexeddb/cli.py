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
import traceback

from dfindexeddb import errors
from dfindexeddb import version
from dfindexeddb.leveldb import record as leveldb_record
from dfindexeddb.indexeddb import chromium
from dfindexeddb.indexeddb import v8


_VALID_PRINTABLE_CHARACTERS = (
    ' abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' +
    '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~.')


class Encoder(json.JSONEncoder):
  """A JSON encoder class for dfindexeddb fields."""
  def default(self, o):
    if dataclasses.is_dataclass(o):
      o_dict = dataclasses.asdict(o)
      #o_dict['__type__'] = o.__class__.__name__
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
    return json.JSONEncoder.default(self, o)


def _Output(structure, to_json=False):
  """Helper method to output parsed structure to stdout."""
  if to_json:
    print(json.dumps(structure, indent=2, cls=Encoder))
  else:
    print(structure)


def IndexeddbCommand(args):
  """The CLI for processing a log/ldb file as indexeddb."""
  for record_path in leveldb_record.LevelDBRecord.FromDir(args.source):
    try:
      record = record_path.record
      record_path.record = chromium.IndexedDBRecord.FromLevelDBRecord(record)
    except(
        errors.ParserError,
        errors.DecoderError,
        NotImplementedError) as err:
      print(
          (f'Error parsing blink value: {err} for {record.__class__.__name__} '
           f'at offset {record.offset} in {record_path.path}'), file=sys.stderr)
      print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)
    _Output(record_path, to_json=args.json)


def App():
  """The CLI app entrypoint for dfindexeddb."""
  parser = argparse.ArgumentParser(
      prog='dfindexeddb',
      description='A cli tool for parsing indexeddb files',
      epilog=f'Version {version.GetVersion()}')
  parser.add_argument(
      '-s', '--source', required=True, type=pathlib.Path,
      help='The source leveldb folder')
  parser.add_argument('--json', action='store_true', help='Output as JSON')
  parser.set_defaults(func=IndexeddbCommand)

  args = parser.parse_args()
  args.func(args)
