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

  def test_decode_bool(self) -> None:
    """Tests the decode_bool method."""
    data = b"\x01"
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeBool()
    self.assertEqual(offset, 0)
    self.assertEqual(result, True)

  def test_decode_string(self) -> None:
    """Tests the decode_string method."""
    data = b"\x00a\x00b"
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeString()
    self.assertEqual(offset, 0)
    self.assertEqual(result, "ab")

  def test_decode_blob_with_length(self) -> None:
    """Tests the decode_blob_with_length method."""
    data = b"\x02\x00a"
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeBlobWithLength()
    self.assertEqual(offset, 0)
    self.assertEqual(result, b"\x00a")

  def test_decode_string_with_length(self) -> None:
    """Tests the decode_string_with_length method."""
    data = b"\x01\x00a"
    stream = io.BytesIO(data)
    decoder = utils.LevelDBDecoder(stream)
    offset, result = decoder.DecodeStringWithLength()
    self.assertEqual(offset, 0)
    self.assertEqual(result, "a")

  def test_decode_sortable_double(self) -> None:
    """Tests the DecodeSortableDouble method."""
    with self.subTest("positive"):
      data = b"\xbf\xf0\x00\x00\x00\x00\x00\x00"
      decoder = utils.LevelDBDecoder(io.BytesIO(data))
      offset, result = decoder.DecodeSortableDouble()
      self.assertEqual(offset, 0)
      self.assertEqual(result, 1.0)

    with self.subTest("negative"):
      data = b"\x40\x0f\xff\xff\xff\xff\xff\xff"
      decoder = utils.LevelDBDecoder(io.BytesIO(data))
      _, result = decoder.DecodeSortableDouble()
      self.assertEqual(result, -1.0)

  def test_decode_sortable_string(self) -> None:
    """Tests the DecodeSortableString method."""
    data = b"\x42\x43\x44\x00"  # "ABC"
    decoder = utils.LevelDBDecoder(io.BytesIO(data))
    offset, result = decoder.DecodeSortableString()
    self.assertEqual(offset, 0)
    self.assertEqual(result, "ABC")

  def test_decode_sortable_binary(self) -> None:
    """Tests the DecodeSortableBinary method."""
    with self.subTest("empty"):
      data = b"\x00"
      decoder = utils.LevelDBDecoder(io.BytesIO(data))
      offset, result = decoder.DecodeSortableBinary()
      self.assertEqual(offset, 0)
      self.assertEqual(result, b"")

    with self.subTest("one chunk ABCDEFGH"):
      data = b"\x09ABCDEFGH\x08"
      decoder = utils.LevelDBDecoder(io.BytesIO(data))
      _, result = decoder.DecodeSortableBinary()
      self.assertEqual(result, b"ABCDEFGH")

    with self.subTest("partial chunk ABC"):
      data = b"\x09ABC\x00\x00\x00\x00\x00\x03"
      decoder = utils.LevelDBDecoder(io.BytesIO(data))
      _, result = decoder.DecodeSortableBinary()
      self.assertEqual(result, b"ABC")


if __name__ == "__main__":
  unittest.main()
