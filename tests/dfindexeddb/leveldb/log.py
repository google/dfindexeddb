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
import pathlib
import struct
import tempfile
import unittest

from dfindexeddb import errors
from dfindexeddb.leveldb import definitions, log


class LogTest(unittest.TestCase):
  """Unit tests for the leveldb log parser."""

  def test_open_log(self) -> None:
    """Tests the log file can be opened."""
    log_file = log.FileReader("./test_data/leveldb/create key/000003.log")
    self.assertIsNotNone(log_file)

  def test_blocks(self) -> None:
    """Tests the GetBlocks method."""
    log_file = log.FileReader(
        "./test_data/leveldb/large logfilerecord/000003.log"
    )
    blocks = list(log_file.GetBlocks())
    for block_number, block in enumerate(blocks):
      self.assertIsInstance(block, log.Block)
      self.assertEqual(block.offset, block_number * log.Block.BLOCK_SIZE)
      self.assertIsInstance(block.data, bytes)

  def test_log_file_record(self) -> None:
    """Tests the GetPhysicalRecords method."""
    log_file = log.FileReader(
        "./test_data/leveldb/large logfilerecord/000003.log"
    )
    physical_records = list(log_file.GetPhysicalRecords())
    self.assertIsInstance(physical_records[0], log.PhysicalRecord)
    self.assertEqual(physical_records[0].base_offset, 0)
    self.assertEqual(
        physical_records[0].record_type,
        definitions.LogFilePhysicalRecordType.FULL,
    )

    self.assertEqual(physical_records[1].base_offset, 0)
    self.assertEqual(
        physical_records[1].record_type,
        definitions.LogFilePhysicalRecordType.FIRST,
    )
    self.assertEqual(physical_records[2].base_offset, 32768)
    self.assertEqual(
        physical_records[2].record_type,
        definitions.LogFilePhysicalRecordType.MIDDLE,
    )
    self.assertEqual(physical_records[3].base_offset, 65536)
    self.assertEqual(
        physical_records[3].record_type,
        definitions.LogFilePhysicalRecordType.MIDDLE,
    )
    self.assertEqual(physical_records[4].base_offset, 98304)
    self.assertEqual(
        physical_records[4].record_type,
        definitions.LogFilePhysicalRecordType.LAST,
    )
    self.assertEqual(physical_records[5].base_offset, 98304)
    self.assertEqual(
        physical_records[5].record_type,
        definitions.LogFilePhysicalRecordType.FULL,
    )
    self.assertTrue(
        all(record.is_valid_checksum for record in physical_records)
    )

  def test_batches(self) -> None:
    """Tests the GetWriteBatches method."""
    log_file = log.FileReader("./test_data/leveldb/100k keys/000004.log")
    batches = list(log_file.GetWriteBatches())
    self.assertIsInstance(batches[0], log.WriteBatch)

    # the first batch starts after the LogFileRecord header which is 7 bytes
    self.assertEqual(batches[0].offset, 7)

    # ths test leveldb was initialised with 1000000 records
    self.assertEqual(batches[-1].sequence_number, 100000)
    self.assertEqual(batches[-1].count, 1)

  def test_key_value_records(self) -> None:
    """Tests the GetKeyValueRecords method."""
    log_file = log.FileReader("./test_data/leveldb/delete large key/000006.log")
    records = list(log_file.GetParsedInternalKeys())
    self.assertIsInstance(records[0], log.ParsedInternalKey)
    self.assertEqual(records[0].key, b"AAAAAAAA" * 1024 * 1024)
    # 7 (log file record header) + 12 (log file batch header) = 19
    self.assertEqual(records[0].offset, 19)
    self.assertEqual(records[0].value, b"")
    self.assertEqual(
        records[0].record_type, definitions.InternalRecordType.DELETED
    )
    self.assertEqual(records[0].sequence_number, 3)

  def test_crc32c_and_mask_vectors(self) -> None:
    """Tests Castagnoli CRC32C check value and LevelDB mask round-trip."""
    raw_crc = log.ComputeCrc32c(b"123456789")
    self.assertEqual(raw_crc, 0xE3069283)
    masked_crc = log.MaskCrc32c(raw_crc)
    self.assertEqual(log.UnmaskCrc32c(masked_crc), raw_crc)

  def test_validate_checksum_on_intact_and_corrupted_records(self) -> None:
    """Tests PhysicalRecord checksum verification and validate_checksum flag."""
    # All intact upstream test logs pass strict checksum verification.
    intact_reader = log.FileReader(
        "./test_data/leveldb/create key/000003.log",
        validate_checksum=True,
    )
    intact_keys = list(intact_reader.GetParsedInternalKeys())
    self.assertGreater(len(intact_keys), 0)

    # Construct a synthetic FULL physical record + 7-byte zero tail padding.
    batch = struct.pack("<QI", 500002, 1) + b"\x01\x02k1\x06value1"
    record_type = int(definitions.LogFilePhysicalRecordType.FULL)
    valid_crc = log.ComputeMaskedCrc32c(record_type, batch)
    intact_frame = (
        struct.pack("<IHB", valid_crc, len(batch), record_type)
        + batch
        + (b"\x00" * log.PhysicalRecord.PHYSICAL_HEADER_LENGTH)
    )

    # Flip 1 bit in the payload without updating the header checksum.
    corrupted_buf = bytearray(intact_frame)
    corrupted_buf[10] ^= 0x01
    corrupted_frame = bytes(corrupted_buf)

    with tempfile.TemporaryDirectory() as tmp_dir:
      intact_path = pathlib.Path(tmp_dir) / "intact.log"
      intact_path.write_bytes(intact_frame)
      parsed_ok = list(
          log.FileReader(intact_path, validate_checksum=True)
          .GetParsedInternalKeys()
      )
      self.assertEqual(len(parsed_ok), 1)
      self.assertEqual(parsed_ok[0].value, b"value1")

      corrupt_path = pathlib.Path(tmp_dir) / "corrupt.log"
      corrupt_path.write_bytes(corrupted_frame)

      # Default validate_checksum=False preserves backward-compatible carving
      # while marking is_valid_checksum=False on the damaged PhysicalRecord.
      default_records = list(
          log.FileReader(corrupt_path).GetPhysicalRecords()
      )
      self.assertEqual(len(default_records), 1)
      self.assertFalse(default_records[0].is_valid_checksum)

      # Strict validate_checksum=True raises ParserError on CRC32C mismatch.
      with self.assertRaises(errors.ParserError):
        list(
            log.FileReader(corrupt_path, validate_checksum=True)
            .GetParsedInternalKeys()
        )

      # Zeroed checksum header with non-zero length/type also fails strict mode.
      zero_crc_frame = (
          struct.pack("<IHB", 0, len(batch), record_type) + batch
      )
      zero_crc_path = pathlib.Path(tmp_dir) / "zero_crc.log"
      zero_crc_path.write_bytes(zero_crc_frame)
      with self.assertRaises(errors.ParserError):
        list(
            log.FileReader(zero_crc_path, validate_checksum=True)
            .GetPhysicalRecords()
        )


if __name__ == "__main__":
  unittest.main()
