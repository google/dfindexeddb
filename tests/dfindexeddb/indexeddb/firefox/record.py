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
"""Unit tests for Firefox IndexedDB encoded sqlite3 databases."""
import unittest

from dfindexeddb.indexeddb.firefox import definitions
from dfindexeddb.indexeddb.firefox import record
from dfindexeddb.indexeddb.firefox import gecko


class FirefoxIndexedDBTest(unittest.TestCase):
  """Unit tests for Firefox IndexedDB encoded sqlite3 databases."""

  def setUp(self):
    self.reader = record.FileReader(
        './test_data/indexeddb/firefox/650921982Itnsdeetx+eBdD.sqlite')

  def test_init(self):
    """Tests the init method."""
    self.assertEqual(self.reader.database_name, 'IndexedDB test')
    self.assertEqual(
        self.reader.origin,
        'file:///Users/Shared/generate_firefox_indexeddb.html')
    self.assertEqual(
        self.reader.metadata_version, 1)
    self.assertEqual(self.reader.last_analyze_time, 0)

  def test_object_stores(self):
    """Tests the ObjectStores method."""
    object_stores = list(self.reader.ObjectStores())
    self.assertEqual(len(object_stores), 2)

    self.assertEqual(object_stores[0].id, 1)
    self.assertEqual(object_stores[0].name, 'test store a')
    self.assertEqual(object_stores[0].key_path, 'id')
    self.assertEqual(object_stores[0].auto_inc, 31)
    self.assertEqual(object_stores[0].database_name, 'IndexedDB test')

  def test_records_by_object_store_id(self):
    """Tests the RecordsByObjectStoreId method."""
    expected_record = record.FirefoxIndexedDBRecord(
        key=gecko.IDBKey(
            offset=0, type=definitions.IndexedDBKeyType.FLOAT, value=-3.14),
        value={'id': -3.14, 'value': {}},
        file_ids=None,
        object_store_id=1,
        object_store_name='test store a',
        database_name='IndexedDB test'
    )
    records = list(self.reader.RecordsByObjectStoreId(1))

    self.assertEqual(records[0], expected_record)

  def test_records(self):
    """Tests the Records method."""
    expected_record = record.FirefoxIndexedDBRecord(
        key=gecko.IDBKey(
            offset=0, type=definitions.IndexedDBKeyType.FLOAT, value=-3.14),
        value={'id': -3.14, 'value': {}},
        file_ids=None,
        object_store_id=1,
        object_store_name='test store a',
        database_name='IndexedDB test'
    )
    records = list(self.reader.Records())
    self.assertEqual(records[0], expected_record)
