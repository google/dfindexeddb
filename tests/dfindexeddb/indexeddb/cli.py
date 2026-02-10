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
"""Unit tests for the CLI in dfindexeddb."""
import argparse
import unittest
from unittest import mock

from dfindexeddb.indexeddb import cli
from dfindexeddb.indexeddb.chromium import definitions as chromium_definitions
from dfindexeddb.indexeddb.chromium import record as chromium_record
from dfindexeddb.indexeddb.chromium import sqlite as chromium_sqlite
from dfindexeddb.indexeddb.firefox import record as firefox_record
from dfindexeddb.indexeddb.firefox import gecko as firefox_gecko
from dfindexeddb.indexeddb.firefox import definitions as firefox_definitions
from dfindexeddb.indexeddb.safari import record as safari_record


class CLITest(unittest.TestCase):
  """Unit tests for the CLI."""

  def setUp(self) -> None:
    """Sets up the test case."""
    self.args = argparse.Namespace(
        source="source_file",
        format="chrome",
        object_store_id=None,
        include_raw_data=False,
        filter_value=None,
        filter_key=None,
        load_blobs=False,
        output="json",
        use_manifest=False,
        use_sequence_number=False,
    )

  def test_matches_filters_no_filters(self) -> None:
    """Tests _MatchesFilters with no filters."""
    record = chromium_sqlite.ChromiumIndexedDBRecord(
        row_id=1,
        object_store_id=1,
        compression_type=0,
        key="key",
        value="val",
        has_blobs=False,
        raw_key=None,
        raw_value=None,
    )
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

  def test_matches_filters_object_store_id(self) -> None:
    """Tests _MatchesFilters with object_store_id filter."""
    record = chromium_sqlite.ChromiumIndexedDBRecord(
        row_id=1,
        object_store_id=1,
        compression_type=0,
        key="key",
        value="val",
        has_blobs=False,
        raw_key=None,
        raw_value=None,
    )
    self.args.object_store_id = 1
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

    self.args.object_store_id = 2
    # pylint: disable=protected-access
    self.assertFalse(cli._MatchesFilters(record, self.args))

  def test_matches_filters_value(self) -> None:
    """Tests _MatchesFilters with value filter."""
    record = chromium_record.ChromiumIndexedDBRecord(
        path="path",
        offset=0,
        key="key",
        value=chromium_record.ObjectStoreDataValue(
            version=1, blob_size=None, blob_offset=None, value="search_me"
        ),
        sequence_number=1,
        type=1,
        level=0,
        recovered=False,
        database_id=1,
        object_store_id=1,
    )
    self.args.filter_value = "search"
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

    self.args.filter_value = "missing"
    # pylint: disable=protected-access
    self.assertFalse(cli._MatchesFilters(record, self.args))

  def test_matches_filters_value_blobs(self) -> None:
    """Tests _MatchesFilters with value filter for records with blobs."""
    record = chromium_record.ChromiumIndexedDBRecord(
        path="path",
        offset=0,
        key="key",
        value=chromium_record.IndexedDBExternalObject(offset=0, entries=[]),
        sequence_number=1,
        type=1,
        level=0,
        recovered=False,
        database_id=1,
        object_store_id=1,
        blobs=[("path/to/blob", "blob_content")],
    )
    self.args.filter_value = "content"
    self.args.load_blobs = True
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

    self.args.filter_value = "missing"
    # pylint: disable=protected-access
    self.assertFalse(cli._MatchesFilters(record, self.args))

  def test_matches_filters_key(self) -> None:
    """Tests _MatchesFilters with key filter."""
    record = chromium_sqlite.ChromiumIndexedDBRecord(
        row_id=1,
        object_store_id=1,
        compression_type=0,
        key=chromium_record.SortableIDBKey(
            offset=0,
            type=chromium_definitions.IDBKeyType.STRING,
            value="my_key",
        ),
        value="val",
        has_blobs=False,
        raw_key=None,
        raw_value=None,
    )
    self.args.filter_key = "my"
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

    self.args.filter_key = "other"
    # pylint: disable=protected-access
    self.assertFalse(cli._MatchesFilters(record, self.args))

  def test_matches_filters_chromium_key(self) -> None:
    """Tests _MatchesFilters with chromium specific key types."""
    idb_key = chromium_record.IDBKey(
        offset=8,
        type=chromium_definitions.IDBKeyType.STRING,
        value="user_key_value",
    )
    key_prefix = chromium_record.KeyPrefix(
        offset=0, database_id=1, object_store_id=1, index_id=1
    )

    os_key = chromium_record.ObjectStoreDataKey(
        offset=0, key_prefix=key_prefix, encoded_user_key=idb_key
    )
    record = chromium_record.ChromiumIndexedDBRecord(
        path="path",
        offset=0,
        key=os_key,
        value="val",
        sequence_number=1,
        type=1,
        level=0,
        recovered=False,
        database_id=1,
        object_store_id=1,
    )
    self.args.filter_key = "user"
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

    record.key = chromium_record.BlobEntryKey(
        offset=0, key_prefix=key_prefix, user_key=idb_key
    )
    # pylint: disable=protected-access
    self.assertTrue(cli._MatchesFilters(record, self.args))

  @mock.patch("dfindexeddb.indexeddb.cli._Output")
  @mock.patch("dfindexeddb.indexeddb.chromium.sqlite.DatabaseReader")
  def test_handle_chromium_db_file(
      self, mock_reader_cls: mock.MagicMock, mock_output: mock.MagicMock
  ) -> None:
    """Tests HandleChromiumDB when source is a file."""
    mock_reader = mock_reader_cls.return_value
    record = chromium_sqlite.ChromiumIndexedDBRecord(
        row_id=1,
        object_store_id=1,
        compression_type=0,
        key=chromium_record.SortableIDBKey(
            offset=0,
            type=chromium_definitions.IDBKeyType.STRING,
            value="key",
        ),
        value="val",
        has_blobs=False,
        raw_key=None,
        raw_value=None,
    )
    mock_reader.Records.return_value = [record]

    args_source = mock.MagicMock()
    args_source.is_file.return_value = True
    args_source.__str__ = mock.MagicMock(  # type: ignore[method-assign]
        return_value="source_file"
    )
    self.args.source = args_source

    cli.HandleChromiumDB(self.args)

    mock_reader_cls.assert_called_once_with("source_file")
    mock_reader.Records.assert_called_once_with(
        include_raw_data=False, load_blobs=False
    )
    mock_output.assert_called_once_with(record, output="json")

  @mock.patch("dfindexeddb.indexeddb.cli._Output")
  @mock.patch("dfindexeddb.indexeddb.chromium.record.FolderReader")
  def test_handle_chromium_db_folder(
      self, mock_reader_cls: mock.MagicMock, mock_output: mock.MagicMock
  ) -> None:
    """Tests HandleChromiumDB when source is a directory."""
    mock_reader = mock_reader_cls.return_value
    record = chromium_record.ChromiumIndexedDBRecord(
        path="path",
        offset=0,
        key="key",
        value="val",
        sequence_number=1,
        type=1,
        level=0,
        recovered=False,
        database_id=1,
        object_store_id=1,
    )
    mock_reader.GetRecords.return_value = [record]

    args_source = mock.MagicMock()
    args_source.is_file.return_value = False
    self.args.source = args_source
    self.args.use_manifest = True

    cli.HandleChromiumDB(self.args)

    mock_reader_cls.assert_called_once_with(args_source)
    mock_reader.GetRecords.assert_called_once_with(
        use_manifest=True,
        use_sequence_number=False,
        include_raw_data=False,
        load_blobs=False,
    )
    mock_output.assert_called_once_with(record, output="json")

  @mock.patch("dfindexeddb.indexeddb.cli._Output")
  @mock.patch("dfindexeddb.indexeddb.firefox.record.FileReader")
  def test_handle_firefox_db(
      self, mock_reader_cls: mock.MagicMock, mock_output: mock.MagicMock
  ) -> None:
    """Tests HandleFirefoxDB."""
    mock_reader = mock_reader_cls.return_value
    idb_key = firefox_gecko.IDBKey(
        offset=0,
        type=firefox_definitions.IndexedDBKeyType.STRING,
        value="key",
    )
    record = firefox_record.FirefoxIndexedDBRecord(
        key=idb_key,
        value="val",
        file_ids=None,
        object_store_id=1,
        object_store_name="store",
        database_name="db",
    )
    mock_reader.Records.return_value = [record]

    self.args.format = "firefox"
    cli.HandleFirefoxDB(self.args)

    mock_reader_cls.assert_called_once_with("source_file")
    mock_reader.Records.assert_called_once_with(
        include_raw_data=False, load_blobs=False
    )
    mock_output.assert_called_once_with(record, output="json")

  @mock.patch("dfindexeddb.indexeddb.cli._Output")
  @mock.patch("dfindexeddb.indexeddb.safari.record.FileReader")
  def test_handle_safari_db(
      self, mock_reader_cls: mock.MagicMock, mock_output: mock.MagicMock
  ) -> None:
    """Tests HandleSafariDB."""
    mock_reader = mock_reader_cls.return_value
    record = safari_record.SafariIndexedDBRecord(
        key="key",
        value="val",
        object_store_id=1,
        object_store_name="store",
        database_name="db",
        record_id=1,
    )
    mock_reader.Records.return_value = [record]

    self.args.format = "safari"
    self.args.source = "source_file"
    cli.HandleSafariDB(self.args)

    mock_reader_cls.assert_called_once_with("source_file")
    mock_reader.Records.assert_called_once_with(
        include_raw_data=False, load_blobs=False
    )
    mock_output.assert_called_once_with(record, output="json")

  @mock.patch("dfindexeddb.indexeddb.cli.HandleChromiumDB")
  def test_db_command_dispatch_chromium(
      self, mock_handler: mock.MagicMock
  ) -> None:
    """Tests DbCommand dispatches to HandleChromiumDB."""
    cli.DbCommand(self.args)
    mock_handler.assert_called_once_with(self.args)

  @mock.patch("dfindexeddb.indexeddb.cli._Output")
  @mock.patch(
      "dfindexeddb.indexeddb.chromium.record.ChromiumIndexedDBRecord.FromFile"
  )
  def test_ldb_command(
      self, mock_from_file: mock.MagicMock, mock_output: mock.MagicMock
  ) -> None:
    """Tests LdbCommand."""
    record = chromium_record.ChromiumIndexedDBRecord(
        path="path",
        offset=0,
        key="key",
        value="val",
        sequence_number=1,
        type=1,
        level=0,
        recovered=False,
        database_id=1,
        object_store_id=1,
    )
    mock_from_file.return_value = [record]

    self.args.source = "source.ldb"
    cli.LdbCommand(self.args)

    mock_from_file.assert_called_once_with(
        "source.ldb", include_raw_data=False, load_blobs=False
    )
    mock_output.assert_called_once_with(record, output="json")

  @mock.patch("dfindexeddb.indexeddb.cli._Output")
  @mock.patch(
      "dfindexeddb.indexeddb.chromium.record.ChromiumIndexedDBRecord.FromFile"
  )
  def test_log_command(
      self, mock_from_file: mock.MagicMock, mock_output: mock.MagicMock
  ) -> None:
    """Tests LogCommand."""
    record = chromium_record.ChromiumIndexedDBRecord(
        path="path",
        offset=0,
        key="key",
        value="val",
        sequence_number=1,
        type=1,
        level=0,
        recovered=False,
        database_id=1,
        object_store_id=1,
    )
    mock_from_file.return_value = [record]

    self.args.source = "source.log"
    cli.LogCommand(self.args)

    mock_from_file.assert_called_once_with(
        "source.log", include_raw_data=False, load_blobs=False
    )
    mock_output.assert_called_once_with(record, output="json")


if __name__ == "__main__":
  unittest.main()
