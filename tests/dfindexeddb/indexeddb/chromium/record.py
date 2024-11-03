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

from dfindexeddb.indexeddb.chromium import record
from dfindexeddb.indexeddb.chromium import definitions


class ChromiumIndexedDBTest(unittest.TestCase):
  """Unit tests for Chromium IndexedDB encoded leveldb databases."""

  def test_parse_key_prefix(self):
    """Tests the KeyPrefix class."""
    expected_key_prefix = record.KeyPrefix(
        offset=0, database_id=1, object_store_id=2, index_id=3)
    key_bytes = b'\x00\x01\x02\x03\x00'
    parsed_key_prefix = record.KeyPrefix.FromBytes(key_bytes)
    self.assertEqual(parsed_key_prefix, expected_key_prefix)

  def test_parse_idbkey(self):
    """Tests the IDBKey class."""
    expected_idbkey = record.IDBKey(
        offset=4, type=definitions.IDBKeyType.NUMBER, value=2.0)
    key_bytes = b'\x03\x00\x00\x00\x00\x00\x00\x00@'
    parsed_idbkey = record.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_idbkey, expected_idbkey)

  def test_parse_idbkeypath(self):
    """Tests the IDBKeyPath class."""
    expected_key = record.IDBKeyPath(
        offset=3, type=definitions.IDBKeyPathType.STRING, value='id')
    key_bytes = b'\x00\x00\x01\x02\x00i\x00d'
    parsed_key = record.IDBKeyPath.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_blob_journal(self):
    """Tests the BlobJournal class"""
    expected_key = record.BlobJournal(
        offset=4, entries=[])
    key_bytes = b''
    parsed_key = record.BlobJournal.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_schema_version_key(self):
    """Tests the SchemaVersionKey."""
    expected_key = record.SchemaVersionKey(
        offset=4,
        key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0))
    expected_value = 5

    record_bytes = ((b'\x00\x00\x00\x00\x00'), (b'\x05'))
    parsed_key = record.SchemaVersionKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_max_database_id_key(self):
    """Tests the MaxDatabaseIdKey."""
    expected_key = record.MaxDatabaseIdKey(
        offset=4, key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0))
    expected_value = 4

    record_bytes = ((b'\x00\x00\x00\x00\x01'), (b'\x04'))
    parsed_key = record.MaxDatabaseIdKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_data_version_key(self):
    """Tests the DataVersionKey."""
    expected_key = record.DataVersionKey(
        offset=4, key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0))
    expected_value = 20

    record_bytes = ((b'\x00\x00\x00\x00\x02'), (b'\x14\x00\x00\x00\x0f'))
    parsed_key = record.DataVersionKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_earliest_sweep_key(self):
    """Tests the EarliestSweepKey."""
    expected_key = record.EarliestSweepKey(
        offset=4, key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0))
    expected_value = 13318143299762026

    record_bytes = ((b'\x00\x00\x00\x00\x05'), (b'j7s\xe0\xc7P/'))
    parsed_key = record.EarliestSweepKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_earliest_compaction_key(self):
    """Tests the EarliestCompactionTimeKey."""
    expected_key = record.EarliestCompactionTimeKey(
        offset=4, key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0))
    expected_value = 13318229420051176

    record_bytes = ((b'\x00\x00\x00\x00\x06'), (b'\xe8\x8a\x9e\xed\xdbP/'))
    parsed_key = record.EarliestCompactionTimeKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_scopes_prefix_key(self):
    """Tests the ScopesPrefixKey."""
    expected_key = record.ScopesPrefixKey(
        offset=4, key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0))
    expected_value = b'\x08\x01'

    record_bytes = ((b'\x00\x00\x00\x002\x00'), (b'\x08\x01'))
    parsed_key = record.ScopesPrefixKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_database_name_key(self):
    """Tests the DatabaseNameKey."""
    expected_key = record.DatabaseNameKey(
        offset=4, key_prefix=record.KeyPrefix(
            offset=0, database_id=0, object_store_id=0, index_id=0),
        origin='file__0@1', database_name='IndexedDB test')
    expected_value = 4

    record_bytes = ((
        b'\x00\x00\x00\x00\xc9\t\x00f\x00i\x00l\x00e\x00_\x00_\x000\x00@\x00'
        b'1\x0e\x00I\x00n\x00d\x00e\x00x\x00e\x00d\x00D\x00B\x00 \x00t\x00e'
        b'\x00s\x00t'), (b'\x04'))
    parsed_key = record.DatabaseNameKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])

    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.GlobalMetaDataKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)

  def test_database_metadata_key(self):
    """Tests the DatabaseMetadataKey."""
    with self.subTest('ORIGIN_NAME'):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          metadata_type=definitions.DatabaseMetaDataKeyType.ORIGIN_NAME)
      expected_value = 'a'

      record_bytes = (b'\x00\x04\x00\x00\x00', b'\x00a')

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('DATABASE_NAME'):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          metadata_type=(definitions.DatabaseMetaDataKeyType
              .DATABASE_NAME))
      expected_value = 'test'

      record_bytes = (b'\x00\x04\x00\x00\x01', b'\x00t\x00e\x00s\x00t')

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('MAX_ALLOCATED_OBJECT_STORE_ID'):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          metadata_type=(definitions.DatabaseMetaDataKeyType
              .MAX_ALLOCATED_OBJECT_STORE_ID))
      expected_value = 2

      record_bytes = (b'\x00\x04\x00\x00\x03', b'\x02')

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('IDB_INTEGER_VERSION'):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          metadata_type=definitions.DatabaseMetaDataKeyType.IDB_INTEGER_VERSION)
      expected_value = 1

      record_bytes = (b'\x00\x04\x00\x00\x04', b'\x01')

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('BLOB_NUMBER_GENERATOR_CURRENT_NUMBER'):
      expected_key = record.DatabaseMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          metadata_type=(definitions.DatabaseMetaDataKeyType
              .BLOB_NUMBER_GENERATOR_CURRENT_NUMBER))
      expected_value = 1

      record_bytes = (b'\x00\x04\x00\x00\x05', b'\x01')

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

  def test_index_metadata_key(self):
    """Tests the IndexMetaDataKey."""
    with self.subTest('INDEX_NAME'):
      expected_key = record.IndexMetaDataKey(
          offset=4, key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1, index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.INDEX_NAME)
      expected_value = 'test index a'

      record_bytes = (
          (b'\x00\x04\x00\x00d\x01\x1f\x00'),
          (b'\x00t\x00e\x00s\x00t\x00 \x00i\x00n\x00d\x00e\x00x\x00 \x00a'))
      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('INDEX_NAME'):
      expected_key = record.IndexMetaDataKey(
          offset=4, key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1, index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.INDEX_NAME)
      expected_value = 'test index a'

      record_bytes = (
          (b'\x00\x04\x00\x00d\x01\x1f\x00'),
          (b'\x00t\x00e\x00s\x00t\x00 \x00i\x00n\x00d\x00e\x00x\x00 \x00a'))
      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('UNIQUE_FLAG'):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.UNIQUE_FLAG)
      expected_value = True

      record_bytes = (b'\x00\x04\x00\x00d\x01\x1f\x01', b'\x00')
      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('KEY_PATH'):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.KEY_PATH)
      expected_value = record.IDBKeyPath(
          offset=3, type=definitions.IDBKeyPathType.STRING, value='test_date')

      record_bytes = (
          b'\x00\x04\x00\x00d\x01\x1f\x02',
          b'\x00\x00\x01\t\x00t\x00e\x00s\x00t\x00_\x00d\x00a\x00t\x00e')

      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('MULTI_ENTRY_FLAG'):
      expected_key = record.IndexMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          index_id=31,
          metadata_type=definitions.IndexMetaDataKeyType.MULTI_ENTRY_FLAG)
      expected_value = True

      record_bytes = (b'\x00\x04\x00\x00d\x01\x1f\x03', b'\x00')

      parsed_key = record.IndexMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

  def test_object_store_meta_data_key(self):
    """Tests the ObjectStoreMetaDataKey."""
    with self.subTest('OBJECT_STORE_NAME'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .OBJECT_STORE_NAME))
      expected_value = 'test store a'

      record_bytes = (
          b'\x00\x04\x00\x002\x01\x00',
          b'\x00t\x00e\x00s\x00t\x00 \x00s\x00t\x00o\x00r\x00e\x00 \x00a')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('KEY_PATH'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .KEY_PATH))
      expected_value = record.IDBKeyPath(
          offset=3,
          type=definitions.IDBKeyPathType.STRING,
          value='id')

      record_bytes = (
          b'\x00\x04\x00\x002\x01\x01',
          b'\x00\x00\x01\x02\x00i\x00d')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('KEY_PATH'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .AUTO_INCREMENT_FLAG))
      expected_value = True

      record_bytes = (
          b'\x00\x04\x00\x002\x01\x02',
          b'\x00')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('IS_EVICTABLE'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .IS_EVICTABLE))
      expected_value = True

      record_bytes = (
          b'\x00\x04\x00\x002\x01\x03',
          b'\x00')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('LAST_VERSION_NUMBER'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .LAST_VERSION_NUMBER))
      expected_value = 3

      record_bytes = (
          b'\x00\x04\x00\x002\x01\x04',
          b'\x03')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('MAXIMUM_ALLOCATED_INDEX_ID'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .MAXIMUM_ALLOCATED_INDEX_ID))
      expected_value = 31

      record_bytes = (
          b'\x00\x04\x00\x002\x01\x05',
          b'\x1f')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('HAS_KEY_PATH'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=definitions.ObjectStoreMetaDataKeyType.HAS_KEY_PATH)
      expected_value = True

      record_bytes = (b'\x00\x04\x00\x002\x01\x06', b'\x01')

      parsed_key = record.ObjectStoreMetaDataKey.FromBytes(record_bytes[0])
      parsed_value = parsed_key.ParseValue(record_bytes[1])
      self.assertEqual(expected_key, parsed_key)
      self.assertEqual(parsed_value, expected_value)

      parsed_key = record.DatabaseMetaDataKey.FromBytes(record_bytes[0])
      self.assertEqual(expected_key, parsed_key)

    with self.subTest('KEY_GENERATOR_CURRENT_NUMBER'):
      expected_key = record.ObjectStoreMetaDataKey(
          offset=4,
          key_prefix=record.KeyPrefix(
              offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_id=1,
          metadata_type=(definitions.ObjectStoreMetaDataKeyType
              .KEY_GENERATOR_CURRENT_NUMBER))
      expected_value = 1

      record_bytes = (b'\x00\x04\x00\x002\x01\x07', b'\x01')

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
            offset=0, database_id=4, object_store_id=0, index_id=0),
          object_store_name='empty store')
    expected_value = 2
    record_bytes = (
        (b'\x00\x04\x00\x00\xc8\x0b\x00e\x00m\x00p\x00t'
         b'\x00y\x00 \x00s\x00t\x00o\x00r\x00e'),
        b'\x02')

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
            offset=0, database_id=1, object_store_id=1, index_id=1),
        encoded_user_key=record.IDBKey(
            offset=4, type=definitions.IDBKeyType.NUMBER, value=3.0))
    expected_value = record.ObjectStoreDataValue(
        version=4,
        is_wrapped=True,
        blob_offset=1,
        blob_size=2303,
        value=None)
    record_bytes = (
        b'\x00\x01\x01\x01\x03\x00\x00\x00\x00\x00\x00\x08@',
        b'\x04\xff\x11\x01\xd0\xa0\x06\x00')

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
            offset=0, database_id=1, object_store_id=1, index_id=2),
        encoded_user_key=record.IDBKey(
            offset=4,
            type=definitions.IDBKeyType.NUMBER,
            value=1.0))
    expected_value = 2

    record_bytes = (
        b'\x00\x01\x01\x02\x03\x00\x00\x00\x00\x00\x00\xf0?', b'\x02')

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
            offset=0, database_id=1, object_store_id=1, index_id=31),
        encoded_user_key=record.IDBKey(
            offset=5,
            type=definitions.IDBKeyType.DATE,
            value=datetime.datetime(2023, 2, 12, 23, 20, 30, 459000)),
            sequence_number=0,
            encoded_primary_key=record.IDBKey(
                offset=3720,
                type=definitions.IDBKeyType.NUMBER, value=4.0))
    expected_value = (
        5,
        record.IDBKey(
          offset=1,
          type=definitions.IDBKeyType.NUMBER,
          value=4.0))

    record_bytes = ((
        b'\x00\x01\x01\x1f\x02\x00\xb0?\xe1~dxB\x00\x03\x00\x00\x00\x00'
        b'\x00\x00\x10@'),
        b'\x05\x03\x00\x00\x00\x00\x00\x00\x10@')

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
            offset=0, database_id=1, object_store_id=1, index_id=3),
        user_key=record.IDBKey(
            offset=4, type=definitions.IDBKeyType.NUMBER, value=3.0))
    expected_value = record.IndexedDBExternalObject(
        offset=0,
        entries=[
            record.ExternalObjectEntry(
                offset=0,
                object_type=definitions.ExternalObjectType.BLOB,
                blob_number=2,
                mime_type='application/vnd.blink-idb-value-wrapper',
                size=102480,
                filename=None,
                last_modified=None,
                token=None)])

    record_bytes = (
      b'\x00\x01\x01\x03\x03\x00\x00\x00\x00\x00\x00\x08@',
      (b'\x00\x02\'\x00a\x00p\x00p\x00l\x00i\x00c\x00a\x00t\x00i\x00o\x00n\x00/'
       b'\x00v\x00n\x00d\x00.\x00b\x00l\x00i\x00n\x00k\x00-\x00i\x00d\x00b\x00-'
       b'\x00v\x00a\x00l\x00u\x00e\x00-\x00w\x00r\x00a\x00p\x00p\x00e\x00r\xd0'
       b'\xa0\x06'))

    parsed_key = record.BlobEntryKey.FromBytes(record_bytes[0])
    parsed_value = parsed_key.ParseValue(record_bytes[1])
    self.assertEqual(expected_key, parsed_key)
    self.assertEqual(parsed_value, expected_value)

    parsed_key = record.IndexedDbKey.FromBytes(record_bytes[0])
    self.assertEqual(parsed_key, expected_key)


if __name__ == '__main__':
  unittest.main()
