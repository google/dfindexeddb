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
"""Unit tests for Chromium IndexedDB encoded leveldb databases."""
import datetime
import unittest

from dfindexeddb.indexeddb.chromium import definitions, record


class ChromiumIndexedDBTest(unittest.TestCase):
  """Unit tests for Chromium IndexedDB encoded leveldb databases."""

  def test_parse_key_prefix(self):
    """Tests the KeyPrefix class."""
    expected_key_prefix = record.KeyPrefix(
        offset=0, database_id=1, object_store_id=2, index_id=3
    )
    key_bytes = bytes.fromhex("0001020300")
    parsed_key_prefix = record.KeyPrefix.FromBytes(key_bytes)
    self.assertEqual(parsed_key_prefix, expected_key_prefix)

  def test_parse_key_prefix_multi_byte_database_id(self):
    """Tests the KeyPrefix class with multi-byte database id."""
    expected_key_prefix = record.KeyPrefix(
        offset=0, database_id=257, object_store_id=2, index_id=3
    )
    key_bytes = bytes.fromhex("2001010203")
    parsed_key_prefix = record.KeyPrefix.FromBytes(key_bytes)
    self.assertEqual(parsed_key_prefix, expected_key_prefix)

  def test_parse_key_prefix_multi_byte_object_store_id(self):
    """Tests the KeyPrefix class with multi-byte object store id."""
    expected_key_prefix = record.KeyPrefix(
        offset=0, database_id=0, object_store_id=257, index_id=3
    )
    key_bytes = bytes.fromhex("0400010103")
    parsed_key_prefix = record.KeyPrefix.FromBytes(key_bytes)
    self.assertEqual(parsed_key_prefix, expected_key_prefix)

  def test_parse_key_prefix_multi_byte_index_id(self):
    """Tests the KeyPrefix class with multi-byte index id."""
    expected_key_prefix = record.KeyPrefix(
        offset=0, database_id=1, object_store_id=2, index_id=257
    )
    key_bytes = bytes.fromhex("0101020101")
    parsed_key_prefix = record.KeyPrefix.FromBytes(key_bytes)
    self.assertEqual(parsed_key_prefix, expected_key_prefix)

  def test_parse_idbkey(self):
    """Tests the IDBKey class."""
    expected_idbkey = record.IDBKey(
        offset=4, type=definitions.IDBKeyType.NUMBER, value=2.0
    )
    key_bytes = bytes.fromhex("030000000000000040")
    parsed_idbkey = record.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_idbkey, expected_idbkey)

  def test_parse_idbkeypath(self):
    """Tests the IDBKeyPath class."""
    expected_key = record.IDBKeyPath(
        offset=3, type=definitions.IDBKeyPathType.STRING, value="id"
    )
    key_bytes = bytes.fromhex("0000010200690064")
    parsed_key = record.IDBKeyPath.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_blob_journal(self):
    """Tests the BlobJournal class"""
    expected_key = record.BlobJournal(offset=4, entries=[])
    key_bytes = b""
    parsed_key = record.BlobJournal.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_schema_version_key(self):
    """Tests the SchemaVersionKey."""
    expected_key = record.SchemaVersionKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
    )
    expected_value = 5

    record_bytes = (bytes.fromhex("0000000000"), bytes.fromhex("05"))
    parsed_key = record.SchemaVersionKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_max_database_id_key(self):
    """Tests the MaxDatabaseIdKey."""
    expected_key = record.MaxDatabaseIdKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
    )
    expected_value = 4

    record_bytes = (bytes.fromhex("0000000001"), bytes.fromhex("04"))
    parsed_key = record.MaxDatabaseIdKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_data_version_key(self):
    """Tests the DataVersionKey."""
    expected_key = record.DataVersionKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
    )
    expected_value = 64424509460

    record_bytes = (bytes.fromhex("0000000002"), bytes.fromhex("140000000f"))
    parsed_key = record.DataVersionKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_earliest_sweep_key(self):
    """Tests the EarliestSweepKey."""
    expected_key = record.EarliestSweepKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
    )
    expected_value = 13318143299762026

    record_bytes = (
        bytes.fromhex("0000000005"),
        bytes.fromhex("6a3773e0c7502f"),
    )
    parsed_key = record.EarliestSweepKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_earliest_compaction_key(self):
    """Tests the EarliestCompactionTimeKey."""
    expected_key = record.EarliestCompactionTimeKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
    )
    expected_value = 13318229420051176

    record_bytes = (
        bytes.fromhex("0000000006"),
        bytes.fromhex("e88a9eeddb502f"),
    )
    parsed_key = record.EarliestCompactionTimeKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_scopes_prefix_key(self):
    """Tests the ScopesPrefixKey."""
    expected_key = record.ScopesPrefixKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
    )
    expected_value = bytes.fromhex("0801")

    record_bytes = (bytes.fromhex("000000003200"), bytes.fromhex("0801"))
    parsed_key = record.ScopesPrefixKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_database_name_key(self):
    """Tests the DatabaseNameKey."""
    expected_key = record.DatabaseNameKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0
        ),
        origin="file__0@1",
        database_name="IndexedDB test",
    )
    expected_value = 4

    record_bytes = (
        bytes.fromhex(
            "00000000c90900660069006c0065005f005f0030004000310e0049006e006400"
            "650078006500640044004200200074006500730074"
        ),
        bytes.fromhex("04"),
    )
    parsed_key = record.DatabaseNameKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_database_metadata_key(self):
    """Tests the DatabaseMetadataKey."""
    with self.subTest("ORIGIN_NAME"):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          metadata_type=definitions.DatabaseMetaDataKeyType.ORIGIN_NAME,
      )
      expected_value = "a"

      record_bytes = (bytes.fromhex("0004000000"), bytes.fromhex("0061"))

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("DATABASE_NAME"):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          metadata_type=(definitions.DatabaseMetaDataKeyType.DATABASE_NAME),
      )
      expected_value = "test"

      record_bytes = (
          bytes.fromhex("0004000001"),
          bytes.fromhex("0074006500730074"),
      )

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("MAX_ALLOCATED_OBJECT_STORE_ID"):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          metadata_type=(
              definitions.DatabaseMetaDataKeyType.MAX_ALLOCATED_OBJECT_STORE_ID
          ),
      )
      expected_value = 2

      record_bytes = (bytes.fromhex("0004000003"), bytes.fromhex("02"))

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("IDB_INTEGER_VERSION"):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          metadata_type=definitions.DatabaseMetaDataKeyType.IDB_INTEGER_VERSION,
      )
      expected_value = 1

      record_bytes = (bytes.fromhex("0004000004"), bytes.fromhex("01"))

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("BLOB_NUMBER_GENERATOR_CURRENT_NUMBER"):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          metadata_type=(
              definitions.DatabaseMetaDataKeyType.BLOB_NUMBER_GENERATOR_CURRENT_NUMBER  # pylint: disable=line-too-long
          ),
      )
      expected_value = 1

      record_bytes = (bytes.fromhex("0004000005"), bytes.fromhex("01"))

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

  def test_index_metadata_key(self):
    """Tests the IndexMetaDataKey."""
    with self.subTest("INDEX_NAME"):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.INDEX_NAME,
      )
      expected_value = "test index a"

      record_bytes = (
          bytes.fromhex("0004000064011f00"),
          bytes.fromhex("007400650073007400200069006e00640065007800200061"),
      )
      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("INDEX_NAME"):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.INDEX_NAME,
      )
      expected_value = "test index a"

      record_bytes = (
          bytes.fromhex("0004000064011f00"),
          bytes.fromhex("007400650073007400200069006e00640065007800200061"),
      )
      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("UNIQUE_FLAG"):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.UNIQUE_FLAG,
      )
      expected_value = True

      record_bytes = (bytes.fromhex("0004000064011f01"), bytes.fromhex("00"))
      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("KEY_PATH"):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.KEY_PATH,
      )
      expected_value = record.IDBKeyPath(
          offset=3, type=definitions.IDBKeyPathType.STRING, value="test_date"
      )

      record_bytes = (
          bytes.fromhex("0004000064011f02"),
          bytes.fromhex("000001090074006500730074005f0064006100740065"),
      )

      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("MULTI_ENTRY_FLAG"):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.MULTI_ENTRY_FLAG,
      )
      expected_value = True

      record_bytes = (bytes.fromhex("0004000064011f03"), bytes.fromhex("00"))

      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

  def test_object_store_meta_data_key(self):
    """Tests the ObjectStoreMetaDataKey."""
    with self.subTest("OBJECT_STORE_NAME"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(
              definitions.ObjectStoreMetaDataKeyType.OBJECT_STORE_NAME
          ),
      )
      expected_value = "test store a"

      record_bytes = (
          bytes.fromhex("00040000320100"),
          bytes.fromhex("0074006500730074002000730074006f0072006500200061"),
      )

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("KEY_PATH"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType.KEY_PATH),
      )
      expected_value = record.IDBKeyPath(
          offset=3, type=definitions.IDBKeyPathType.STRING, value="id"
      )

      record_bytes = (
          bytes.fromhex("00040000320101"),
          bytes.fromhex("0000010200690064"),
      )

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("KEY_PATH"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(
              definitions.ObjectStoreMetaDataKeyType.AUTO_INCREMENT_FLAG
          ),
      )
      expected_value = True

      record_bytes = (bytes.fromhex("00040000320102"), bytes.fromhex("00"))

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("IS_EVICTABLE"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType.IS_EVICTABLE),
      )
      expected_value = True

      record_bytes = (bytes.fromhex("00040000320103"), bytes.fromhex("00"))

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("LAST_VERSION_NUMBER"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(
              definitions.ObjectStoreMetaDataKeyType.LAST_VERSION_NUMBER
          ),
      )
      expected_value = 3

      record_bytes = (bytes.fromhex("00040000320104"), bytes.fromhex("03"))

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("MAXIMUM_ALLOCATED_INDEX_ID"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(
              definitions.ObjectStoreMetaDataKeyType.MAXIMUM_ALLOCATED_INDEX_ID
          ),
      )
      expected_value = 31

      record_bytes = (bytes.fromhex("00040000320105"), bytes.fromhex("1f"))

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("HAS_KEY_PATH"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=definitions.ObjectStoreMetaDataKeyType.HAS_KEY_PATH,
      )
      expected_value = True

      record_bytes = (bytes.fromhex("00040000320106"), bytes.fromhex("01"))

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest("KEY_GENERATOR_CURRENT_NUMBER"):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0
          ),
          object_store_id=1,
          metadata_type=(
              definitions.ObjectStoreMetaDataKeyType.KEY_GENERATOR_CURRENT_NUMBER  # pylint: disable=line-too-long
          ),
      )
      expected_value = 1

      record_bytes = (bytes.fromhex("00040000320107"), bytes.fromhex("01"))

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

  # def test_object_store_free_list_key(self):
  #   """Tests the ObjectStoreFreeListKey"""
  #   pass

  # def test_index_free_list_key(self):
  #   """Tests the IndexFreeListKey"""
  #   pass

  def test_object_store_names_key(self):
    """Tests the ObjectStoreNamesKey."""
    expected_key = record.ObjectStoreNamesKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=4, object_store_id=0, index_id=0
        ),
        object_store_name="empty store",
    )
    expected_value = 2
    record_bytes = (
        bytes.fromhex(
            "00040000c80b0065006d007000740079002000730074006f00720065"
        ),
        bytes.fromhex("02"),
    )

    parsed_key = record.ObjectStoreNamesKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])
    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  # def test_index_names_key(self):
  #   """Tests the IndexNamesKey."""
  #   pass

  def test_object_store_data_key(self):
    """Tests the ObjectStoreDataKey."""
    expected_key = record.ObjectStoreDataKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=1, object_store_id=1, index_id=1
        ),
        encoded_user_key=record.IDBKey(
            offset=4, type=definitions.IDBKeyType.NUMBER, value=3.0
        ),
    )
    expected_value = record.ObjectStoreDataValue(
        version=4, blob_offset=0, blob_size=102480, value=None
    )
    record_bytes = (
        bytes.fromhex("00010101030000000000000840"),
        bytes.fromhex("04ff1101d0a00600"),
    )

    parsed_key = record.ObjectStoreDataKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])
    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.IndexedDbKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_exists_entry_key(self):
    """Tests the ExistsEntryKey."""
    expected_key = record.ExistsEntryKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=1, object_store_id=1, index_id=2
        ),
        encoded_user_key=record.IDBKey(
            offset=4, type=definitions.IDBKeyType.NUMBER, value=1.0
        ),
    )
    expected_value = 2

    record_bytes = (
        bytes.fromhex("0001010203000000000000f03f"),
        bytes.fromhex("02"),
    )

    parsed_key = record.ExistsEntryKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])
    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.IndexedDbKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_index_data_key(self):
    """Tests the IndexDataKey."""
    expected_key = record.IndexDataKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=1, object_store_id=1, index_id=31
        ),
        encoded_user_key=record.IDBKey(
            offset=5,
            type=definitions.IDBKeyType.DATE,
            value=datetime.datetime(2023, 2, 12, 23, 20, 30, 459000),
        ),
        sequence_number=0,
        encoded_primary_key=record.IDBKey(
            offset=3720, type=definitions.IDBKeyType.NUMBER, value=4.0
        ),
    )
    expected_value = (
        5,
        record.IDBKey(offset=1, type=definitions.IDBKeyType.NUMBER, value=4.0),
    )

    record_bytes = (
        bytes.fromhex("0001011f0200b03fe17e64784200030000000000001040"),
        bytes.fromhex("05030000000000001040"),
    )

    parsed_key = record.IndexDataKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])
    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.IndexedDbKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_blob_entry_key(self):
    """Tests the BlobEntryKey and the IndexedDBExternalObject."""
    expected_key = record.BlobEntryKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=1, object_store_id=1, index_id=3
        ),
        user_key=record.IDBKey(
            offset=4, type=definitions.IDBKeyType.NUMBER, value=3.0
        ),
    )
    expected_value = record.IndexedDBExternalObject(
        offset=0,
        entries=[
            record.ExternalObjectEntry(
                offset=0,
                object_type=definitions.ExternalObjectType.BLOB,
                blob_number=2,
                mime_type="application/vnd.blink-idb-value-wrapper",
                size=102480,
                filename=None,
                last_modified=None,
                token=None,
            )
        ],
    )

    record_bytes = (
        bytes.fromhex("00010103030000000000000840"),
        bytes.fromhex(
            "000227006100700070006c00690063006100740069006f006e002f0076006e00"
            "64002e0062006c0069006e006b002d006900640062002d00760061006c007500"
            "65002d0077007200610070007000650072d0a006"
        ),
    )

    parsed_key = record.BlobEntryKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])
    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.IndexedDbKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)


if __name__ == "__main__":
  unittest.main()
