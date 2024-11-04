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
"""Unit tests for LevelDB Manifest files."""
import unittest

#from dfindexeddb.leveldb import definitions
from dfindexeddb.leveldb import log
from dfindexeddb.leveldb import descriptor


class DescriptorTests(unittest.TestCase):
  """Unit tests for the Descriptor/MANIFEST parser."""

  def test_open_manifest(self):
    """Tests the manifest file can be opened."""
    manifest_file = descriptor.FileReader(
        './test_data/leveldb/create key/MANIFEST-000002')
    self.assertIsNotNone(manifest_file)

  def test_blocks(self):
    """Tests the GetBlocks method."""
    manifest_file = descriptor.FileReader(
        './test_data/leveldb/create large key/MANIFEST-000002')
    blocks = list(manifest_file.GetBlocks())
    for block_number, block in enumerate(blocks):
      self.assertIsInstance(block, log.Block)
      self.assertEqual(
          block.offset, block_number*log.Block.BLOCK_SIZE)
      self.assertIsInstance(block.data, bytes)

  def test_versionedit(self):
    """Tests the GetVersionEdits method."""
    manifest_file = descriptor.FileReader(
        './test_data/leveldb/large logfilerecord/MANIFEST-000002')
    version_edits = list(manifest_file.GetVersionEdits())
    self.assertEqual(len(version_edits), 2)
    self.assertEqual(version_edits[0].comparator, b'leveldb.BytewiseComparator')
    self.assertEqual(version_edits[0].offset, 7)

    self.assertEqual(version_edits[1].offset, 42)
    self.assertEqual(version_edits[1].log_number, 3)
    self.assertEqual(version_edits[1].prev_log_number, 0)
    self.assertEqual(version_edits[1].next_file_number, 4)
    self.assertEqual(version_edits[1].last_sequence, 0)
    self.assertEqual(version_edits[1].compact_pointers, [])
    self.assertEqual(version_edits[1].new_files, [])
    self.assertEqual(version_edits[1].deleted_files, [])

  def test_versions(self):
    """Tests the GetVersions method."""
    manifest_file = descriptor.FileReader(
        './test_data/leveldb/100k keys delete/MANIFEST-000002')
    versions = list(manifest_file.GetVersions())
    self.assertEqual(len(versions), 3)
    self.assertEqual(versions[0].active_files, {})
    self.assertEqual(versions[0].deleted_files, {})
    self.assertEqual(versions[0].current_log, None)
    self.assertEqual(versions[0].last_sequence, None)

    self.assertEqual(len(versions[2].active_files), 1)
    self.assertIn(2, versions[2].active_files)
    self.assertIn('000005.ldb', versions[2].active_files[2])
    self.assertEqual(versions[2].deleted_files, {})
    self.assertEqual(versions[2].current_log, '000004.log')
    self.assertEqual(versions[2].last_sequence, 85673)

  def test_latestversion(self):
    """Tests the GetLatestVersion method."""
    manifest_file = descriptor.FileReader(
        './test_data/leveldb/100k keys delete/MANIFEST-000002')
    latest_version = manifest_file.GetLatestVersion()
    self.assertIsNotNone(latest_version)
    self.assertEqual(len(latest_version.active_files), 1)
    self.assertIn(2, latest_version.active_files)
    self.assertIn('000005.ldb', latest_version.active_files[2])
    self.assertEqual(latest_version.deleted_files, {})
    self.assertEqual(latest_version.current_log, '000004.log')
    self.assertEqual(latest_version.last_sequence, 85673)


if __name__ == '__main__':
  unittest.main()
