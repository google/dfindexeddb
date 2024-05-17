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
"""A CLI tool for leveldb files."""
import argparse
import dataclasses
from datetime import datetime
import json
import pathlib

from dfindexeddb import version
from dfindexeddb.leveldb import descriptor
from dfindexeddb.leveldb import ldb
from dfindexeddb.leveldb import log
from dfindexeddb.leveldb import record


_VALID_PRINTABLE_CHARACTERS = (
    ' abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' +
    '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~.')


class Encoder(json.JSONEncoder):
  """A JSON encoder class for dfleveldb fields."""

  def default(self, o):
    """Returns a serializable object for o."""
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
    if isinstance(o, set):
      return list(o)
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
  """The CLI for processing leveldb folders."""
  for leveldb_record in record.FolderReader(
      args.source).GetRecords(
          use_manifest=args.use_manifest,
          use_sequence_number=args.use_sequence_number):
    _Output(leveldb_record, output=args.output)


def LdbCommand(args):
  """The CLI for processing ldb files."""
  ldb_file = ldb.FileReader(args.source)

  if args.structure_type == 'blocks':
    # Prints block information.
    for block in ldb_file.GetBlocks():
      _Output(block, output=args.output)

  elif args.structure_type == 'records' or not args.structure_type:
    # Prints key value record information.
    for key_value_record in ldb_file.GetKeyValueRecords():
      _Output(key_value_record, output=args.output)

  else:
    print(f'{args.structure_type} is not supported for ldb files.')


def LogCommand(args):
  """The CLI for processing log files."""
  log_file = log.FileReader(args.source)

  if args.structure_type == 'blocks':
    # Prints block information.
    for block in log_file.GetBlocks():
      _Output(block, output=args.output)

  elif args.structure_type == 'physical_records':
    # Prints log file physical record information.
    for log_file_record in log_file.GetPhysicalRecords():
      _Output(log_file_record, output=args.output)

  elif args.structure_type == 'write_batches':
    # Prints log file batch information.
    for batch in log_file.GetWriteBatches():
      _Output(batch, output=args.output)

  elif (args.structure_type in ('parsed_internal_key', 'records')
        or not args.structure_type):
    # Prints key value record information.
    for internal_key_record in log_file.GetParsedInternalKeys():
      _Output(internal_key_record, output=args.output)

  else:
    print(f'{args.structure_type} is not supported for log files.')


def DescriptorCommand(args):
  """The CLI for processing descriptor (MANIFEST) files."""
  manifest_file = descriptor.FileReader(args.source)

  if args.version_history:
    for levels in manifest_file.GetVersions():
      _Output(levels, output=args.output)

  elif args.structure_type == 'blocks':
    # Prints block information.
    for block in manifest_file.GetBlocks():
      _Output(block, output=args.output)

  elif args.structure_type == 'physical_records':
    # Prints log file physical record information.
    for log_file_record in manifest_file.GetPhysicalRecords():
      _Output(log_file_record, output=args.output)

  elif (args.structure_type == 'versionedit'
        or not args.structure_type):
    for version_edit in manifest_file.GetVersionEdits():
      _Output(version_edit, output=args.output)

  else:
    print(f'{args.structure_type} is not supported for descriptor files.')

def App():
  """The CLI app entrypoint for parsing leveldb files."""
  parser = argparse.ArgumentParser(
      prog='dfleveldb',
      description='A cli tool for parsing leveldb files',
      epilog=f'Version {version.GetVersion()}')

  subparsers = parser.add_subparsers()

  parser_db = subparsers.add_parser(
      'db', help='Parse a directory as leveldb.')
  parser_db.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
      help='The source leveldb directory')
  recover_group = parser_db.add_mutually_exclusive_group()
  recover_group.add_argument(
      '--use_manifest',
      action='store_true',
      help='Use manifest file to determine active/deleted records.')
  recover_group.add_argument(
      '--use_sequence_number',
      action='store_true',
      help=(
          'Use sequence number and file offset to determine active/deleted '
          'records.'))
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

  parser_log = subparsers.add_parser(
      'log', help='Parse a leveldb log file.')
  parser_log.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
      help='The source leveldb file')
  parser_log.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  parser_log.add_argument(
      '-t',
      '--structure_type',
      choices=[
          'blocks',
          'physical_records',
          'write_batches',
          'parsed_internal_key'],
      help='Parses the specified structure.  Default is parsed_internal_key.')
  parser_log.set_defaults(func=LogCommand)

  parser_ldb = subparsers.add_parser(
      'ldb', help='Parse a leveldb table (.ldb) file.')
  parser_ldb.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
      help='The source leveldb file')
  parser_ldb.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  parser_ldb.add_argument(
      '-t',
      '--structure_type',
      choices=[
          'blocks',
          'records'],
      help='Parses the specified structure.  Default is records.')
  parser_ldb.set_defaults(func=LdbCommand)

  parser_descriptor = subparsers.add_parser(
      'descriptor', help='Parse a leveldb descriptor (MANIFEST) file.')
  parser_descriptor.add_argument(
      '-s', '--source',
      required=True,
      type=pathlib.Path,
      help='The source leveldb file')
  parser_descriptor.add_argument(
      '-o',
      '--output',
      choices=[
          'json',
          'jsonl',
          'repr'],
      default='json',
      help='Output format.  Default is json')
  db_group = parser_descriptor.add_mutually_exclusive_group()
  db_group.add_argument(
      '-t',
      '--structure_type',
      choices=[
          'blocks', 'physical_records', 'versionedit'],
      help='Parses the specified structure.  Default is versionedit.')
  db_group.add_argument(
      '-v',
      '--version_history',
      action='store_true',
      help='Parses the leveldb version history.')
  parser_descriptor.set_defaults(func=DescriptorCommand)

  args = parser.parse_args()

  if not hasattr(args, 'func'):
    parser.print_usage()
  else:
    args.func(args)
