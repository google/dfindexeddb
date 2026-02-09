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
import json
import pathlib
from datetime import datetime
from typing import Any

from dfindexeddb import utils, version
from dfindexeddb.indexeddb import types
from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.indexeddb.chromium import sqlite
from dfindexeddb.indexeddb.chromium import record as chromium_record
from dfindexeddb.indexeddb.firefox import gecko
from dfindexeddb.indexeddb.firefox import record as firefox_record
from dfindexeddb.indexeddb.safari import record as safari_record

_VALID_PRINTABLE_CHARACTERS = (
    " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    + "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~."
)


class Encoder(json.JSONEncoder):
  """A JSON encoder class for dfindexeddb fields."""

  def default(self, o):  # type: ignore[no-untyped-def]
    if dataclasses.is_dataclass(o):
      o_dict = utils.asdict(o)
      return o_dict
    if isinstance(o, (bytes, bytearray)):
      out = []
      for x in o:
        if chr(x) not in _VALID_PRINTABLE_CHARACTERS:
          out.append(f"\\x{x:02X}")
        else:
          out.append(chr(x))
      return "".join(out)
    if isinstance(o, datetime):
      return o.isoformat()
    if isinstance(o, types.Undefined):
      return "<undefined>"
    if isinstance(o, types.JSArray):
      return o.__dict__
    if isinstance(o, types.Null):
      return "<null>"
    if isinstance(o, set):
      return list(o)
    if isinstance(o, types.RegExp):
      return str(o)
    if isinstance(o, enum.Enum):
      return o.name
    return json.JSONEncoder.default(self, o)


def _Output(structure: Any, output: str) -> None:
  """Helper method to output parsed structure to stdout.

  Args:
    structure: The structure to output.
    output: The output format.
  """
  if output == "json":
    print(json.dumps(structure, indent=2, cls=Encoder))
  elif output == "jsonl":
    print(json.dumps(structure, cls=Encoder))
  elif output == "repr":
    print(structure)


def BlinkCommand(args: argparse.Namespace) -> None:
  """The CLI for processing a file as a blink-encoded value.

  Args:
    args: The arguments for processing the blink-encoded value.
  """
  with open(args.source, "rb") as fd:
    buffer = fd.read()
    blink_value = blink.V8ScriptValueDecoder.FromBytes(buffer)
    _Output(blink_value, output=args.output)


def GeckoCommand(args: argparse.Namespace) -> None:
  """The CLI for processing a file as a gecko-encoded value.

  Args:
    args: The arguments for processing the gecko-encoded value.
  """
  with open(args.source, "rb") as fd:
    buffer = fd.read()
    blink_value = gecko.JSStructuredCloneDecoder.FromBytes(buffer)
    _Output(blink_value, output=args.output)


def _MatchesFilters(record: Any, args: argparse.Namespace) -> bool:
  """Returns True if the record matches the filter criteria.

  Supported filters:
  * object_store_id - filters by object store ID
  * filter_key - filters by key
  * filter_value - filters by value

  Args:
    record: The record to check for filtering.
    args: The arguments containing filter criteria.

  Returns:
    True if the record matches the filter criteria or no filters are set, False
        otherwise.
  """
  if (
      args.object_store_id is not None
      and record.object_store_id != args.object_store_id
  ):
    return False

  if args.filter_value is not None:
    if isinstance(record.value, chromium_record.IndexedDBExternalObject):
      blobs = getattr(record, "blobs", []) or []
      if all(args.filter_value not in str(blob_data) for _, blob_data in blobs):
        return False

    # Skip Chromium LevelDB metadata records
    elif isinstance(
        record, chromium_record.ChromiumIndexedDBRecord
    ) and not isinstance(
        record.value,
        (
            chromium_record.ObjectStoreDataValue,
            chromium_record.IndexedDBExternalObject,
        ),
    ):
      return False

    elif args.filter_value not in str(record.value):
      return False

  if args.filter_key is not None:
    if isinstance(record.key, chromium_record.ObjectStoreDataKey):
      key_val = record.key.encoded_user_key.value
    elif isinstance(record.key, chromium_record.BlobEntryKey):
      key_val = record.key.user_key.value

    # Skip other Chromium LevelDB key types
    elif isinstance(record, chromium_record.ChromiumIndexedDBRecord):
      return False

    else:
      key_val = getattr(record.key, "value", record.key)

    if args.filter_key not in str(key_val):
      return False

  return True


def HandleChromiumDB(args: argparse.Namespace) -> None:
  """The handler for processing a directory/file as Chromium IndexedDB.

  If the source is a directory, it will process as a LevelDB based IndexedDB.
  If the source is a file, it will process as a SQLite based IndexedDB.

  Args:
    args: The arguments for processing the Chromium IndexedDB.
  """
  if args.source.is_file():
    reader = sqlite.DatabaseReader(str(args.source))
    if args.object_store_id is not None:
      records: Any = reader.RecordsByObjectStoreId(
          args.object_store_id,
          include_raw_data=args.include_raw_data,
          load_blobs=args.load_blobs,
      )
    else:
      records = reader.Records(
          include_raw_data=args.include_raw_data,
          load_blobs=args.load_blobs,
      )
  else:
    records = chromium_record.FolderReader(args.source).GetRecords(
        use_manifest=args.use_manifest,
        use_sequence_number=args.use_sequence_number,
        include_raw_data=args.include_raw_data,
        load_blobs=args.load_blobs,
    )

  for record in records:
    if _MatchesFilters(record, args):
      _Output(record, output=args.output)


def HandleFirefoxDB(args: argparse.Namespace) -> None:
  """The handler for processing a file as Firefox IndexedDB.

  Args:
    args: The arguments for processing the Firefox IndexedDB.
  """
  reader = firefox_record.FileReader(str(args.source))
  if args.object_store_id is not None:
    records = reader.RecordsByObjectStoreId(
        args.object_store_id,
        include_raw_data=args.include_raw_data,
        load_blobs=args.load_blobs,
    )
  else:
    records = reader.Records(
        include_raw_data=args.include_raw_data,
        load_blobs=args.load_blobs,
    )

  for record in records:
    if _MatchesFilters(record, args):
      _Output(record, output=args.output)


def HandleSafariDB(args: argparse.Namespace) -> None:
  """The handler for processing a file as Safari IndexedDB.

  Args:
    args: The arguments for processing the Safari IndexedDB.
  """
  reader = safari_record.FileReader(str(args.source))
  if args.object_store_id is not None:
    records = reader.RecordsByObjectStoreId(
        args.object_store_id,
        include_raw_data=args.include_raw_data,
        load_blobs=args.load_blobs,
    )
  else:
    records = reader.Records(
        include_raw_data=args.include_raw_data,
        load_blobs=args.load_blobs,
    )

  for record in records:
    if _MatchesFilters(record, args):
      _Output(record, output=args.output)


def DbCommand(args: argparse.Namespace) -> None:
  """The CLI for processing a file/directory as IndexedDB.

  Args:
    args: The arguments for processing the IndexedDB.
  """
  if args.format in ("chrome", "chromium"):
    HandleChromiumDB(args)
  elif args.format == "firefox":
    HandleFirefoxDB(args)
  elif args.format == "safari":
    HandleSafariDB(args)


def LdbCommand(args: argparse.Namespace) -> None:
  """The CLI for processing a LevelDB table (.ldb) file as IndexedDB.

  Args:
    args: The arguments for processing the LevelDB table.
  """
  for db_record in chromium_record.ChromiumIndexedDBRecord.FromFile(
      args.source,
      include_raw_data=args.include_raw_data,
      load_blobs=args.load_blobs,
  ):
    if _MatchesFilters(db_record, args):
      _Output(db_record, output=args.output)


def LogCommand(args: argparse.Namespace) -> None:
  """The CLI for processing a LevelDB log file as IndexedDB.

  Args:
    args: The arguments for processing the LevelDB log file.
  """
  for db_record in chromium_record.ChromiumIndexedDBRecord.FromFile(
      args.source,
      include_raw_data=args.include_raw_data,
      load_blobs=args.load_blobs,
  ):
    if _MatchesFilters(db_record, args):
      _Output(db_record, output=args.output)


def App() -> None:
  """The CLI app entrypoint for dfindexeddb."""
  parser = argparse.ArgumentParser(
      prog="dfindexeddb",
      description="A cli tool for parsing IndexedDB files",
      epilog=f"Version {version.GetVersion()}",
  )

  subparsers = parser.add_subparsers()

  parser_blink = subparsers.add_parser(
      "blink", help="Parse a file as a blink-encoded value."
  )
  parser_blink.add_argument(
      "-s",
      "--source",
      required=True,
      type=pathlib.Path,
      help="The source file.",
  )
  parser_blink.add_argument(
      "-o",
      "--output",
      choices=["json", "jsonl", "repr"],
      default="json",
      help="Output format.  Default is json.",
  )
  parser_blink.set_defaults(func=BlinkCommand)

  parser_gecko = subparsers.add_parser(
      "gecko", help="Parse a file as a gecko-encoded value."
  )
  parser_gecko.add_argument(
      "-s",
      "--source",
      required=True,
      type=pathlib.Path,
      help="The source file.",
  )
  parser_gecko.add_argument(
      "-o",
      "--output",
      choices=["json", "jsonl", "repr"],
      default="json",
      help="Output format.  Default is json.",
  )
  parser_gecko.set_defaults(func=GeckoCommand)

  parser_db = subparsers.add_parser(
      "db", help="Parse a directory/file as IndexedDB."
  )
  parser_db.add_argument(
      "-s",
      "--source",
      required=True,
      type=pathlib.Path,
      help=(
          "The source IndexedDB folder (for chrome/chromium) "
          "or sqlite3 file (for firefox/safari)."
      ),
  )
  recover_group = parser_db.add_mutually_exclusive_group()
  recover_group.add_argument(
      "--use_manifest",
      action="store_true",
      help="Use manifest file to determine active/deleted records.",
  )
  recover_group.add_argument(
      "--use_sequence_number",
      action="store_true",
      help=(
          "Use sequence number and file offset to determine active/deleted "
          "records."
      ),
  )
  parser_db.add_argument(
      "-f",
      "--format",
      required=True,
      choices=["chromium", "chrome", "firefox", "safari"],
      help="The type of IndexedDB to parse.",
  )
  parser_db.add_argument(
      "--object_store_id",
      type=int,
      help="The object store ID to filter by.",
  )
  parser_db.add_argument(
      "--include_raw_data",
      action="store_true",
      help="Include raw key and value bytes for each record in the output.",
  )
  parser_db.add_argument(
      "--load_blobs",
      action="store_true",
      default=False,
      help="Load blob data, if available for each record in the output.",
  )
  parser_db.add_argument(
      "-o",
      "--output",
      choices=["json", "jsonl", "repr"],
      default="json",
      help="Output format.  Default is json.",
  )
  parser_db.add_argument(
      "--filter_value",
      type=str,
      help=(
          "Only output records where the value contains this string. "
          "Values are normalized to strings before comparison."
      ),
  )
  parser_db.add_argument(
      "--filter_key",
      type=str,
      help=(
          "Only output records where the key contains this string. "
          "Keys are normalized to strings before comparison."
      ),
  )
  parser_db.set_defaults(func=DbCommand)

  parser_ldb = subparsers.add_parser(
      "ldb", help="Parse a ldb file as IndexedDB."
  )
  parser_ldb.add_argument(
      "-s",
      "--source",
      required=True,
      type=pathlib.Path,
      help="The source .ldb file.",
  )
  parser_ldb.add_argument(
      "-o",
      "--output",
      choices=["json", "jsonl", "repr"],
      default="json",
      help="Output format.  Default is json.",
  )
  parser_ldb.add_argument(
      "--object_store_id",
      type=int,
      help="The object store ID to filter by.",
  )
  parser_ldb.add_argument(
      "--include_raw_data",
      action="store_true",
      help="Include raw key and value bytes for each record in the output.",
  )
  parser_ldb.add_argument(
      "--load_blobs",
      action="store_true",
      default=False,
      help="Load blob data, if available for each record in the output.",
  )
  parser_ldb.add_argument(
      "--filter_value",
      type=str,
      help=(
          "Only output records where the value contains this string. "
          "Values are normalized to strings before comparison."
      ),
  )
  parser_ldb.add_argument(
      "--filter_key",
      type=str,
      help=(
          "Only output records where the key contains this string. "
          "Keys are normalized to strings before comparison."
      ),
  )
  parser_ldb.set_defaults(func=LdbCommand)

  parser_log = subparsers.add_parser(
      "log", help="Parse a log file as IndexedDB."
  )
  parser_log.add_argument(
      "-s",
      "--source",
      required=True,
      type=pathlib.Path,
      help="The source .log file.",
  )
  parser_log.add_argument(
      "-o",
      "--output",
      choices=["json", "jsonl", "repr"],
      default="json",
      help="Output format.  Default is json.",
  )
  parser_log.add_argument(
      "--object_store_id",
      type=int,
      help="The object store ID to filter by.",
  )
  parser_log.add_argument(
      "--include_raw_data",
      action="store_true",
      help="Include raw key and value bytes for each record in the output.",
  )
  parser_log.add_argument(
      "--load_blobs",
      action="store_true",
      default=False,
      help="Load blob data, if available for each record in the output.",
  )
  parser_log.add_argument(
      "--filter_value",
      type=str,
      help=(
          "Only output records where the value contains this string. "
          "Values are normalized to strings before comparison."
      ),
  )
  parser_log.add_argument(
      "--filter_key",
      type=str,
      help=(
          "Only output records where the key contains this string. "
          "Keys are normalized to strings before comparison."
      ),
  )
  parser_log.set_defaults(func=LogCommand)

  args: argparse.Namespace = parser.parse_args()
  if hasattr(args, "func"):
    args.func(args)
  else:
    parser.print_help()
