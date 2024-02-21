#!/usr/bin/env python3
"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# -*- coding: utf-8 -*-
"""Dumps the contents of leveldb log and ldb files in a IndexedDB folder."""
import pathlib
from pprint import pprint
import traceback
from typing import Any

import click
import leveldb

from dfindexeddb.indexeddb import blink
from dfindexeddb.indexeddb import chromium
from dfindexeddb import errors
from dfindexeddb.leveldb import ldb
from dfindexeddb.leveldb import log


def Cmp(a: Any, b: Any) -> int:
  """Basic comparator used by the leveldb library.
  
  Note: the real comparator function is alot more involved.
  """
  if a < b:
    return -1
  if a > b:
    return 1
  return 0


@click.group()
@click.pass_context
@click.argument('indexeddb_path', type=click.Path(exists=True))
def Cli(ctx, indexeddb_path):
  """The main cli."""
  ctx.ensure_object(dict)
  ctx.obj['indexeddb_path'] = indexeddb_path


@Cli.command(name='native')
@click.pass_context
def RunNative(ctx):
  """Runs the leveldb library on the leveldb."""
  db = leveldb.LevelDB(  #pylint: disable=c-extension-no-member
      ctx.obj['indexeddb_path'], comparator=('idb_cmp1', Cmp))
  for record in db.RangeIter():
    print(record)

    idbkey = chromium.IndexedDbKey.FromBytes(record[0])
    print(idbkey)

    value = idbkey.ParseValue(record[1])
    print(value)


@Cli.command(name='parser')
@click.pass_context
def RunParser(ctx):
  """Runs the parser on the leveldb."""
  indexeddb_path = ctx.obj['indexeddb_path']
  for filename in pathlib.Path(indexeddb_path).iterdir():
    if filename.name.startswith('.'):
      continue
    if filename.name.endswith('.log'):
      idb_file_records = list(
          log.LogFileReader(filename.as_posix()).GetKeyValueRecords())
    elif filename.name.endswith('.ldb'):
      idb_file_records = list(
          ldb.LdbFileReader(filename.as_posix()).GetKeyValueRecords())
    else:
      continue

    for record in idb_file_records:
      print('[Record]', record)
      idbkey = chromium.IndexedDbKey.FromBytes(
          record.key, base_offset=record.offset)

      if record.type == 0:
        print('[Key (Deleted)]', idbkey)
      else:
        print('[Key]', idbkey)

        value = idbkey.ParseValue(record.value)
        print('[Value]', value)

        if not isinstance(idbkey, chromium.ObjectStoreDataKey):
          continue

        # The ObjectStoreDataKey value should decode as a 2-tuple comprising
        # a version integer and a SSV as a raw byte string
        if not (isinstance(value, tuple) and len(value) == 2 and
            isinstance(value[1], bytes)):
          continue

        try:
          value = blink.V8ScriptValueDecoder.FromBytes(value[1])
          print('[Blink value]', end=' ')
          pprint(value)
        except (errors.ParserError, errors.DecoderError) as err:
          print(f'[Error] {err}: {traceback.format_exc()}')


if __name__ == '__main__':
  Cli()  #pylint: disable=no-value-for-parameter
