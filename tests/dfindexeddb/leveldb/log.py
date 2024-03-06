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
"""Unit tests for LevelDB Log (.log) files."""
import unittest

from dfindexeddb.leveldb import definitions
from dfindexeddb.leveldb import log


class LogTest(unittest.TestCase):
  """Unit tests for the leveldb log parser."""

  def test_open_log(self):
    """Tests the log file can be opened."""
    log_file = log.FileReader('./test_data/leveldb/create key/000003.log')
    self.assertIsNotNone(log_file)

  def test_blocks(self):
    """Tests the GetBlocks method."""
    log_file = log.FileReader(
        './test_data/leveldb/large logfilerecord/000003.log')
    blocks = list(log_file.GetBlocks())
    for block_number, block in enumerate(blocks):
      self.assertIsInstance(block, log.Block)
      self.assertEqual(
          block.offset, block_number*log.Block.BLOCK_SIZE)
      self.assertIsInstance(block.data, bytes)

  def test_log_file_record(self):
    """Tests the GetPhysicalRecords method."""
    log_file = log.FileReader(
        './test_data/leveldb/large logfilerecord/000003.log')
    physical_records = list(log_file.GetPhysicalRecords())
    self.assertIsInstance(physical_records[0], log.PhysicalRecord)
    self.assertEqual(physical_records[0].base_offset, 0)
    self.assertEqual(
        physical_records[0].record_type,
        definitions.LogFilePhysicalRecordType.FULL)

    self.assertEqual(physical_records[1].base_offset, 0)
    self.assertEqual(
        physical_records[1].record_type,
        definitions.LogFilePhysicalRecordType.FIRST)
    self.assertEqual(physical_records[2].base_offset, 32768)
    self.assertEqual(
        physical_records[2].record_type,
        definitions.LogFilePhysicalRecordType.MIDDLE)
    self.assertEqual(physical_records[3].base_offset, 65536)
    self.assertEqual(
        physical_records[3].record_type,
        definitions.LogFilePhysicalRecordType.MIDDLE)
    self.assertEqual(physical_records[4].base_offset, 98304)
    self.assertEqual(
        physical_records[4].record_type,
        definitions.LogFilePhysicalRecordType.LAST)
    self.assertEqual(physical_records[5].base_offset, 98304)
    self.assertEqual(
        physical_records[5].record_type,
        definitions.LogFilePhysicalRecordType.FULL)

  def test_batches(self):
    """Tests the GetWriteBatches method."""
    log_file = log.FileReader('./test_data/leveldb/100k keys/000004.log')
    batches = list(log_file.GetWriteBatches())
    self.assertIsInstance(batches[0], log.WriteBatch)

    # the first batch starts after the LogFileRecord header which is 7 bytes
    self.assertEqual(batches[0].offset, 7)

    # ths test leveldb was initialised with 1000000 records
    self.assertEqual(batches[-1].sequence_number, 100000)
    self.assertEqual(batches[-1].count, 1)

  def test_key_value_records(self):
    """Tests the GetKeyValueRecords method."""
    log_file = log.FileReader(
        './test_data/leveldb/delete large key/000006.log')
    records = list(log_file.GetKeyValueRecords())
    self.assertIsInstance(records[0], log.ParsedInternalKey)
    self.assertEqual(records[0].key, b'AAAAAAAA'*1024*1024)
    # 7 (log file record header) + 12 (log file batch header) = 19
    self.assertEqual(records[0].offset, 19)
    self.assertEqual(records[0].value, b'')
    self.assertEqual(
        records[0].record_type, definitions.InternalRecordType.DELETED)
    self.assertEqual(records[0].sequence_number, 3)


if __name__ == '__main__':
  unittest.main()
