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
"""Dumps the contents of a LevelDB table (.ldb) file."""
import click

from dfindexeddb.leveldb import ldb


@click.group()
@click.pass_context
@click.argument('ldb_filename', type=click.Path(exists=True))
def Cli(ctx, ldb_filename):
  """The main cli."""
  ldbfile = ldb.LdbFileReader(ldb_filename)
  ctx.ensure_object(dict)
  ctx.obj['ldb_filename'] = ldb_filename
  ctx.obj['ldbfile'] = ldbfile


@Cli.command(name='blocks')
@click.pass_context
def LdbBlocks(ctx):
  """Prints block information."""
  for block in ctx.obj['ldbfile'].LdbBGetBlockslocks():
    print(block)


@Cli.command(name='records')
@click.pass_context
def LdbRecords(ctx):
  """Prints key value record information."""
  for records in ctx.obj['ldbfile'].GetKeyValueRecords():
    print(records)


if __name__ == '__main__':
  Cli()  #pylint: disable=no-value-for-parameter
