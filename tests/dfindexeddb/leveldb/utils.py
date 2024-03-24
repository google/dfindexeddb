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
"""Unit tests for utility classes."""
import io
import unittest

from dfindexeddb.leveldb import utils


class LevelDBDecoderTest(unittest.TestCase):
  """Unit tests for the LevelDBDecoder class."""

  def test_decode_bool(self):
    """Tests the decode_bool method."""
    data = b'\x01'
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeBool()
    self.assertEqual(offset, 0)
    self.assertEqual(result, True)

  def test_decode_string(self):
    """Tests the decode_string method."""
    data = b'\x00a\x00b'
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeString()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 'ab')

  def test_decode_blob_with_length(self):
    """Tests the decode_blob_with_length method."""
    data = b'\x02\x00a'
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeBlobWithLength()
    self.assertEqual(offset, 0)
    self.assertEqual(result, b'\x00a')

  def test_decode_string_with_length(self):
    """Tests the decode_string_with_length method."""
    data = b'\x01\x00a'
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeStringWithLength()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 'a')


if __name__ == '__main__':
  unittest.main()
