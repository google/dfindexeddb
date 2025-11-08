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
"""Unit tests for Safari IndexedDB encoded sqlite3 databases."""
import datetime
import unittest

from dfindexeddb.indexeddb import types
from dfindexeddb.indexeddb.safari import definitions, record, webkit


class SafariIndexedDBTest(unittest.TestCase):
  """Unit tests for Safari IndexedDB encoded sqlite3 databases."""

  def setUp(self):
    self.db = record.FileReader(
        "./test_data/indexeddb/safari/17.3.1/IndexedDB.sqlite3"
    )

  def test_nonexistent_record(self):
    """Tests for a nonexistent record."""
    parsed_record = self.db.RecordById(0)
    self.assertIsNone(parsed_record)

  def test_undefined_record(self):
    """Tests for an IndexedDB record with an undefined value."""
    expected_record = record.IndexedDBRecord(
        key=10,
        value={"id": 10, "value": types.Undefined()},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=1,
    )
    parsed_record = self.db.RecordById(1)
    self.assertEqual(parsed_record, expected_record)

  def test_null_record(self):
    """Tests for an IndexedDB record with a Null value."""
    expected_record = record.IndexedDBRecord(
        key=11,
        value={"id": 11, "value": types.Null()},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=2,
    )
    parsed_record = self.db.RecordById(2)
    self.assertEqual(parsed_record, expected_record)

  def test_zero_record(self):
    """Tests for an IndexedDB record with a 0 value."""
    expected_record = record.IndexedDBRecord(
        key=12,
        value={"id": 12, "value": 0},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=3,
    )
    parsed_record = self.db.RecordById(3)
    self.assertEqual(parsed_record, expected_record)

  def test_one_record(self):
    """Tests for an IndexedDB record with a 1 value."""
    expected_record = record.IndexedDBRecord(
        key=13,
        value={"id": 13, "value": 1},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=4,
    )
    parsed_record = self.db.RecordById(4)
    self.assertEqual(parsed_record, expected_record)

  def test_number_record(self):
    """Tests for an IndexedDB record with a number value."""
    expected_record = record.IndexedDBRecord(
        key=14,
        value={"id": 14, "value": 123},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=5,
    )
    parsed_record = self.db.RecordById(5)
    self.assertEqual(parsed_record, expected_record)

  def test_true_record(self):
    """Tests for an IndexedDB record with a true value."""
    expected_record = record.IndexedDBRecord(
        key=15,
        value={"id": 15, "value": True},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=6,
    )
    parsed_record = self.db.RecordById(6)
    self.assertEqual(parsed_record, expected_record)

  def test_false_record(self):
    """Tests for an IndexedDB record with a false value."""
    expected_record = record.IndexedDBRecord(
        key=16,
        value={"id": 16, "value": False},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=7,
    )
    parsed_record = self.db.RecordById(7)
    self.assertEqual(parsed_record, expected_record)

  def test_true_object_record(self):
    """Tests for an IndexedDB record with a true object value."""
    expected_record = record.IndexedDBRecord(
        key=17,
        value={"id": 17, "value": True},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=8,
    )
    parsed_record = self.db.RecordById(8)
    self.assertEqual(parsed_record, expected_record)

  def test_false_object_record(self):
    """Tests for an IndexedDB record with a false object value."""
    expected_record = record.IndexedDBRecord(
        key=18,
        value={"id": 18, "value": False},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=9,
    )
    parsed_record = self.db.RecordById(9)
    self.assertEqual(parsed_record, expected_record)

  def test_double_record(self):
    """Tests for an IndexedDB record with a double value."""
    expected_record = record.IndexedDBRecord(
        key=19,
        value={"id": 19, "value": 3.14},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=10,
    )
    parsed_record = self.db.RecordById(10)
    self.assertEqual(parsed_record, expected_record)

  def test_double_object_record(self):
    """Tests for an IndexedDB record with a double object value."""
    expected_record = record.IndexedDBRecord(
        key=20,
        value={"id": 20, "value": 3.14},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=11,
    )
    parsed_record = self.db.RecordById(11)
    self.assertEqual(parsed_record, expected_record)

  def test_bigint_record(self):
    """Tests for an IndexedDB record with a bigint value."""
    expected_record = record.IndexedDBRecord(
        key=21,
        value={"id": 21, "value": 12300000000000001048576},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=12,
    )
    parsed_record = self.db.RecordById(12)
    self.assertEqual(parsed_record, expected_record)

  def test_date_record(self):
    """Tests for an IndexedDB record with a date value."""
    expected_record = record.IndexedDBRecord(
        key=22,
        value={
            "id": 22,
            "value": datetime.datetime(
                year=2023,
                month=2,
                day=12,
                hour=23,
                minute=20,
                second=30,
                microsecond=456000,
            ),
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=13,
    )
    parsed_record = self.db.RecordById(13)
    self.assertEqual(parsed_record, expected_record)

  def test_string_record(self):
    """Tests for an IndexedDB record with a string value."""
    expected_record = record.IndexedDBRecord(
        key=23,
        value={"id": 23, "value": "test string value"},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=14,
    )
    parsed_record = self.db.RecordById(14)
    self.assertEqual(parsed_record, expected_record)

  def test_string_object_record(self):
    """Tests for an IndexedDB record with a string object value."""
    expected_record = record.IndexedDBRecord(
        key=24,
        value={"id": 24, "value": "test string object"},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=15,
    )
    parsed_record = self.db.RecordById(15)
    self.assertEqual(parsed_record, expected_record)

  def test_empty_string_record(self):
    """Tests for an IndexedDB record with an empty string value."""
    expected_record = record.IndexedDBRecord(
        key=25,
        value={"id": 25, "value": ""},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=16,
    )
    parsed_record = self.db.RecordById(16)
    self.assertEqual(parsed_record, expected_record)

  def test_empty_string_object_record(self):
    """Tests for an IndexedDB record with an empty string object value."""
    expected_record = record.IndexedDBRecord(
        key=26,
        value={"id": 26, "value": ""},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=17,
    )
    parsed_record = self.db.RecordById(17)
    self.assertEqual(parsed_record, expected_record)

  def test_set_record(self):
    """Tests for an IndexedDB record with a set value."""
    expected_set = types.JSSet()
    for i in range(1, 4):
      expected_set.values.add(i)

    expected_record = record.IndexedDBRecord(
        key=27,
        value={"id": 27, "value": expected_set},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=18,
    )
    parsed_record = self.db.RecordById(18)
    self.assertEqual(parsed_record, expected_record)

  def test_map_record(self):
    """Tests for an IndexedDB record with an empty map value."""
    expected_record = record.IndexedDBRecord(
        key=28,
        value={"id": 28, "value": {}},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=19,
    )
    parsed_record = self.db.RecordById(19)
    self.assertEqual(parsed_record, expected_record)

  def test_regexp_record(self):
    """Tests for an IndexedDB record with a regexp value."""
    expected_record = record.IndexedDBRecord(
        key=29,
        value={"id": 29, "value": types.RegExp(pattern="", flags="")},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=20,
    )
    parsed_record = self.db.RecordById(20)
    self.assertEqual(parsed_record, expected_record)

  def test_empty_object_record(self):
    """Tests for an IndexedDB record with an empty object value."""
    expected_record = record.IndexedDBRecord(
        key=30,
        value={"id": 30, "value": {}},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=21,
    )
    parsed_record = self.db.RecordById(21)
    self.assertEqual(parsed_record, expected_record)

  def test_mixed_object_record(self):
    """Tests for an IndexedDB record with mixed values within an object."""
    expected_test_array = types.JSArray()
    for value in [123, 456, "abc", "def"]:
      expected_test_array.values.append(value)
    expected_set = types.JSSet()
    for i in range(1, 4):
      expected_set.values.add(i)

    expected_record = record.IndexedDBRecord(
        key=1,
        value={
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
            "test_set": expected_set,
            "test_map": {"a": 1, "b": 2, "c": 3},
            "test_regexp": types.RegExp("\\w+", ""),
            "test_array": expected_test_array,
            "test_object": {
                "name": {"first": "Jane", "last": "Doe"},
                "age": 21,
            },
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=22,
    )
    parsed_record = self.db.RecordById(22)
    self.assertEqual(parsed_record, expected_record)

  def test_nested_object_record(self):
    """Tests for an IndexedDB record with a nested object value."""
    expected_record = record.IndexedDBRecord(
        key=2,
        value={
            "id": 2,
            "test_date": datetime.datetime(2023, 2, 12, 23, 20, 30, 457000),
            "test_nested_array": {
                "level_id": 1,
                "child": {
                    "level_id": 2,
                    "child": {
                        "level_id": 3,
                        "child": {
                            "level_id": 4,
                            "child": {
                                "level_id": 5,
                                "child": {
                                    "level_id": 6,
                                    "child": {"level_id": 7},
                                },
                            },
                        },
                    },
                },
            },
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=23,
    )
    parsed_record = self.db.RecordById(23)
    self.assertEqual(parsed_record, expected_record)

  def test_buffer_record(self):
    """Tests for an IndexedDB record with a buffer value."""
    expected_record = record.IndexedDBRecord(
        key=3,
        value={
            "id": 3,
            "test_date": datetime.datetime(2023, 2, 12, 23, 20, 30, 458000),
            "buffer": b"*" * 1024 + b"\x00" * 99 * 1024,
            "buffer_view": webkit.ArrayBufferView(
                array_buffer_view_subtag=(
                    definitions.ArrayBufferViewSubtag.UINT8_ARRAY
                ),
                buffer=b"*" * 1024 + b"\x00" * 99 * 1024,
                offset=0,
                length=100 * 1024,
            ),
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=24,
    )
    parsed_record = self.db.RecordById(24)
    self.assertEqual(parsed_record, expected_record)

  def test_buffer_view_record(self):
    """Tests for an IndexedDB record with a buffer view value."""
    expected_record = record.IndexedDBRecord(
        key=4,
        value={
            "id": 4,
            "test_date": datetime.datetime(2023, 2, 12, 23, 20, 30, 459000),
            "view": webkit.ArrayBufferView(
                array_buffer_view_subtag=(
                    definitions.ArrayBufferViewSubtag.UINT8_ARRAY
                ),
                buffer=b"\x29" * 1000 * 1024,
                offset=0,
                length=1000 * 1024,
            ),
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=25,
    )
    parsed_record = self.db.RecordById(25)
    self.assertEqual(parsed_record, expected_record)

  def test_date_key_record(self):
    """Tests for an IndexedDB record with a date in the key."""
    expected_record = record.IndexedDBRecord(
        key=datetime.datetime(2023, 2, 12, 23, 20, 30, 456000),
        value={
            "id": datetime.datetime(2023, 2, 12, 23, 20, 30, 456000),
            "value": {},
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=26,
    )
    parsed_record = self.db.RecordById(26)
    self.assertEqual(parsed_record, expected_record)

  def test_number_key_record(self):
    """Tests for an IndexedDB record with a number in the key."""
    expected_record = record.IndexedDBRecord(
        key=-3.14,
        value={"id": -3.14, "value": {}},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=27,
    )
    parsed_record = self.db.RecordById(27)
    self.assertEqual(parsed_record, expected_record)

  def test_string_key_record(self):
    """Tests for an IndexedDB record with a string in the key."""
    expected_record = record.IndexedDBRecord(
        key="test string key",
        value={"id": "test string key", "value": {}},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=28,
    )
    parsed_record = self.db.RecordById(28)
    self.assertEqual(parsed_record, expected_record)

  def test_buffer_key_record(self):
    """Tests for an IndexedDB record with a buffer in the key."""
    expected_record = record.IndexedDBRecord(
        key=b"\x00\x00\x00",
        value={
            "id": webkit.ArrayBufferView(
                array_buffer_view_subtag=(
                    definitions.ArrayBufferViewSubtag.UINT8_ARRAY
                ),
                buffer=b"\x00\x00\x00",
                offset=0,
                length=3,
            ),
            "value": {},
        },
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=29,
    )
    parsed_record = self.db.RecordById(29)
    self.assertEqual(parsed_record, expected_record)

  def test_array_key_record(self):
    """Tests for an IndexedDB record with an array in the key."""
    expected_test_array = types.JSArray()
    for value in [1, 2, 3]:
      expected_test_array.values.append(value)
    expected_record = record.IndexedDBRecord(
        key=[1.0, 2.0, 3.0],
        value={"id": expected_test_array, "value": {}},
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        record_id=30,
    )
    parsed_record = self.db.RecordById(30)
    self.assertEqual(parsed_record, expected_record)
