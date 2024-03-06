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
"""Unit tests for LevelDB Table (.ldb) files."""
import unittest

from dfindexeddb.leveldb import definitions
from dfindexeddb.leveldb import ldb


class LDBTest(unittest.TestCase):
  """Unit tests for the leveldb ldb parser."""

  def test_init_ldb(self):
    """Tests initializing a Ldb FileReader."""
    ldb_file = ldb.FileReader('./test_data/leveldb/100k keys/000005.ldb')
    self.assertIsNotNone(ldb_file)

  def test_blocks(self):
    """Tests the blocks method."""
    ldb_file = ldb.FileReader('./test_data/leveldb/100k keys/000005.ldb')
    blocks = list(ldb_file.GetBlocks())
    first_block = blocks[0]

    self.assertIsInstance(first_block, ldb.Block)
    self.assertEqual(first_block.block_offset, 0)
    self.assertEqual(first_block.length, 1721)
    self.assertTrue(first_block.IsSnappyCompressed())

  def test_records(self):
    """Tests the records method."""
    ldb_file = ldb.FileReader('./test_data/leveldb/100k keys/000005.ldb')

    records = list(ldb_file.GetKeyValueRecords())
    self.assertIsInstance(records[0], ldb.KeyValueRecord)
    self.assertEqual(records[0].key, b'\x00\x00\x00\x00')
    self.assertEqual(records[0].value, b'test value\x00\x00\x00\x00')
    self.assertEqual(records[0].sequence_number, 0)
    self.assertEqual(
        records[0].record_type, definitions.InternalRecordType.VALUE)

  def test_range_iter(self):
    """Tests the RangeIter method."""
    ldb_file = ldb.FileReader('./test_data/leveldb/100k keys/000005.ldb')

    range_iter_records = list(ldb_file.RangeIter())
    self.assertIsInstance(range_iter_records[0], tuple)
    self.assertIsInstance(range_iter_records[0][0], bytes)
    self.assertEqual(range_iter_records[0][0], b'\x00\x00\x00\x00')
    self.assertIsInstance(range_iter_records[0][1], bytes)
    self.assertEqual(range_iter_records[0][1], b'test value\x00\x00\x00\x00')

if __name__ == '__main__':
  unittest.main()
