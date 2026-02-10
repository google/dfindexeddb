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
from typing import cast

from dfindexeddb.indexeddb.firefox import definitions, gecko, record


class FirefoxIndexedDBTest(unittest.TestCase):
  """Unit tests for Firefox IndexedDB encoded sqlite3 databases."""

  def setUp(self) -> None:
    self.reader = record.FileReader(
        "./test_data/indexeddb/firefox/650921982Itnsdeetx+eBdD.sqlite"
    )

  def test_init(self) -> None:
    """Tests the init method."""
    self.assertEqual(self.reader.database_name, "IndexedDB test")
    self.assertEqual(
        self.reader.origin,
        "file:///Users/Shared/generate_firefox_indexeddb.html",
    )
    self.assertEqual(self.reader.metadata_version, 1)
    self.assertEqual(self.reader.last_analyze_time, 0)

  def test_object_stores(self) -> None:
    """Tests the ObjectStores method."""
    object_stores = list(self.reader.ObjectStores())
    self.assertEqual(len(object_stores), 2)

    self.assertEqual(object_stores[0].id, 1)
    self.assertEqual(object_stores[0].name, "test store a")
    self.assertEqual(object_stores[0].key_path, "id")
    self.assertEqual(object_stores[0].auto_inc, 31)
    self.assertEqual(object_stores[0].database_name, "IndexedDB test")

  def test_records_by_object_store_id(self) -> None:
    """Tests the RecordsByObjectStoreId method."""
    expected_record = record.FirefoxIndexedDBRecord(
        key=gecko.IDBKey(
            offset=0, type=definitions.IndexedDBKeyType.FLOAT, value=-3.14
        ),
        value={"id": -3.14, "value": {}},
        file_ids=None,
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        blobs=None,
    )
    records = list(self.reader.RecordsByObjectStoreId(1))

    self.assertEqual(records[0], expected_record)

  def test_records(self) -> None:
    """Tests the Records method."""
    expected_record = record.FirefoxIndexedDBRecord(
        key=gecko.IDBKey(
            offset=0, type=definitions.IndexedDBKeyType.FLOAT, value=-3.14
        ),
        value={"id": -3.14, "value": {}},
        file_ids=None,
        object_store_id=1,
        object_store_name="test store a",
        database_name="IndexedDB test",
        blobs=None,
    )
    records = list(self.reader.Records())
    self.assertEqual(records[0], expected_record)

  def test_records_with_blobs(self) -> None:
    """Tests the Records method with blobs."""
    records = list(self.reader.Records(load_blobs=True))
    record_with_blob = next((r for r in records if r.key.value == 4.0), None)
    self.assertIsNotNone(record_with_blob)
    self.assertIsNotNone(record_with_blob.blobs)  # type: ignore[union-attr]
    blobs = cast(list[record.FirefoxBlobInfo], record_with_blob.blobs)  # type: ignore[union-attr]  #  pylint: disable=line-too-long
    self.assertEqual(len(blobs), 1)
    self.assertEqual(blobs[0].file_id, "2")
    self.assertIsNotNone(blobs[0].blob_data)

  def test_records_with_raw_data(self) -> None:
    """Tests the Records method with raw data."""
    with self.subTest("include_raw_data=True"):
      records_with_raw = list(self.reader.Records(include_raw_data=True))
      self.assertGreater(len(records_with_raw), 0)
      for rec in records_with_raw:
        self.assertIsInstance(rec.raw_key, bytes)
        self.assertIsInstance(rec.raw_value, (bytes, type(None), int))

    with self.subTest("include_raw_data=False"):
      records_no_raw = list(self.reader.Records(include_raw_data=False))
      self.assertEqual(len(records_with_raw), len(records_no_raw))
      for rec in records_no_raw:
        self.assertIsNone(rec.raw_key)
        self.assertIsNone(rec.raw_value)


if __name__ == "__main__":
  unittest.main()
