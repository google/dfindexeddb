# -*- coding: utf-8 -*-
# Copyright 2026 Google LLC
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
"""Unit tests for Chromium IndexedDB encoded sqlite3 databases."""
import datetime
import unittest

from dfindexeddb.indexeddb import types
from dfindexeddb.indexeddb.chromium import sqlite


class ChromiumSQLiteIndexedDBTest(unittest.TestCase):
  """Unit tests for Chromium IndexedDB encoded sqlite3 databases."""

  def setUp(self):
    self.reader = sqlite.DatabaseReader(
        "./test_data/indexeddb/chrome/osx_144_64/file__0/sample"
    )
    expected_test_array = types.JSArray()
    for value in [123, 456, "abc", "def"]:
      expected_test_array.values.append(value)
    expected_set = types.JSSet()
    for i in range(1, 4):
      expected_set.values.add(i)
    self.expected_value = {
        "id": 1,
        "test_undef": types.Undefined(),
        "test_null": types.Null(),
        "test_bool_true": True,
        "test_bool_false": False,
        "test_string": "a string value",
        "test_number": 3.14,
        "test_string_object": "a string object",
        "test_number_object": 3.14,
        "test_boolean_true_object": True,
        "test_boolean_false_object": False,
        "test_bigint": 12300000000000001048576,
        "test_date": datetime.datetime(2023, 2, 12, 23, 20, 30, 456000),
        "test_set": {1, 2, 3},
        "test_map": {"a": 1, "b": 2, "c": 3},
        "test_regexp": types.RegExp("\\w+", "0"),
        "test_array": expected_test_array,
        "test_object": {
            "name": {"first": "Jane", "last": "Doe"},
            "age": 21,
        },
    }

  def test_object_stores(self):
    """Tests the ObjectStores method."""
    object_stores = list(self.reader.ObjectStores())
    self.assertEqual(object_stores[0].id, 1)
    self.assertEqual(object_stores[0].name, "test store a")
    self.assertEqual(object_stores[0].key_path, b"i\x00d\x00")
    self.assertEqual(object_stores[0].key_generator_current_number, 1)
    self.assertEqual(object_stores[0].auto_increment, 0)

  def test_records(self):
    """Tests the Records method."""
    records = list(self.reader.Records())
    self.assertEqual(len(records), 4)
    self.assertEqual(records[0].row_id, 1)
    self.assertEqual(records[0].object_store_id, 1)
    self.assertEqual(records[0].compression_type, 0)
    self.assertFalse(records[0].has_blobs)
    self.assertEqual(records[0].key.value, 1.0)
    self.assertEqual(records[0].value, self.expected_value)
    self.assertIsNone(records[0].raw_key)
    self.assertIsNone(records[0].raw_value)

  def test_records_by_object_store_id(self):
    """Tests the RecordsByObjectStoreId method."""
    records = list(self.reader.RecordsByObjectStoreId(1))
    self.assertEqual(len(records), 4)
    self.assertEqual(records[0].row_id, 1)
    self.assertEqual(records[0].object_store_id, 1)
    self.assertEqual(records[0].compression_type, 0)
    self.assertFalse(records[0].has_blobs)
    self.assertEqual(records[0].key.value, 1.0)
    self.assertEqual(records[0].value, self.expected_value)
    self.assertIsNone(records[0].raw_key)
    self.assertIsNone(records[0].raw_value)


if __name__ == "__main__":
  unittest.main()
