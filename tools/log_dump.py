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
"""Dumps the contents of a LevelDB log (.log) file."""
import click

from dfindexeddb.leveldb import log


@click.group()
@click.pass_context
@click.argument('log_filename', type=click.Path(exists=True))
def Cli(ctx, log_filename):
  """The main cli."""
  logfile = log.LogFileReader(log_filename)
  ctx.ensure_object(dict)
  ctx.obj['log_filename'] = log_filename
  ctx.obj['logfile'] = logfile


@Cli.command(name='blocks')
@click.pass_context
def LogBlocks(ctx):
  """Prints block information."""
  for block in ctx.obj['logfile'].GetBlocks():
    print(block)


@Cli.command(name='physical_records')
@click.pass_context
def PhysicalRecords(ctx):
  """Prints log file physical record information."""
  for log_file_record in ctx.obj['logfile'].GetPhysicalRecords():
    print(log_file_record)


@Cli.command(name='batches')
@click.pass_context
def LogWriteBatches(ctx):
  """Prints log file batch information."""
  for batch in ctx.obj['logfile'].GetWriteBatches():
    print(batch)


@Cli.command(name='records')
@click.pass_context
def LogKeyValueRecords(ctx):
  """Prints key value record information."""
  for records in ctx.obj['logfile'].GetKeyValueRecords():
    print(records)


if __name__ == '__main__':
  Cli()  #pylint: disable=no-value-for-parameter
