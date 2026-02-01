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
"""Unittests for utility classes."""
import io
import struct
import unittest

from dfindexeddb import errors, utils


class TestStreamDecoder(unittest.TestCase):
  """Unit tests for the StreamDecoder class."""

  def test_init(self):
    """Tests the init method."""
    data = b"test"
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    self.assertEqual(decoder.stream, stream)

  def test_num_remaining_bytes(self):
    """Tests the num_remaining_bytes method."""
    data = b"test"
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    self.assertEqual(decoder.NumRemainingBytes(), 4)

  def test_read_bytes(self):
    """Tests the read_bytes method."""
    data = b"test decoder"
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)

    with self.subTest("all bytes"):
      offset, result = decoder.ReadBytes()
      self.assertEqual(offset, 0)
      self.assertEqual(result, data)

    with self.subTest("some bytes"):
      decoder.stream.seek(0)
      offset, result = decoder.ReadBytes(4)
      self.assertEqual(offset, 0)
      self.assertEqual(result, b"test")

    with self.subTest("value error"):
      stream.seek(0)
      with self.assertRaises(errors.DecoderError):
        decoder.ReadBytes(20)

  def test_peek_bytes(self):
    """Tests the peek_bytes method."""
    data = b"test"
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.PeekBytes(4)
    self.assertEqual(offset, 0)
    self.assertEqual(result, b"test")
    self.assertEqual(decoder.stream.tell(), 0)

  def test_decode_int(self):
    """Tests the decode_int method."""

    with self.subTest("little endian unsigned"):
      data = struct.pack("<i", 123456789)
      stream = io.BytesIO(data)
      decoder = utils.StreamDecoder(stream)
      offset, result = decoder.DecodeInt()
      self.assertEqual(offset, 0)
      self.assertEqual(result, 123456789)

    with self.subTest("big endian unsigned integer"):
      data = struct.pack(">I", 123456789)
      stream = io.BytesIO(data)
      decoder = utils.StreamDecoder(stream)
      offset, result = decoder.DecodeInt(byte_order="big", signed=False)
      self.assertEqual(offset, 0)
      self.assertEqual(result, 123456789)

  def test_decode_uint8(self):
    """Tests the decode_uint8 method."""
    data = struct.pack("B", 123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeUint8()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 123)

  def test_decode_uint16(self):
    """Tests the decode_uint16 method."""
    data = struct.pack("<H", 123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeUint16()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 123)

  def test_decode_uint24(self):
    """Tests the decode_uint8 method."""
    data = struct.pack("<I", 123)[:3]
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeUint24()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 123)

  def test_decode_uint32(self):
    """Tests the decode_uint32 method."""
    data = struct.pack("<I", 123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeUint32()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 123)

  def test_decode_uint48(self):
    """Tests the decode_uint48 method."""
    data = struct.pack("<Q", 123)[:6]
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeUint48()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 123)

  def test_decode_uint64(self):
    """Tests the decode_uint64 method."""
    data = struct.pack("<Q", 123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeUint64()
    self.assertEqual(offset, 0)
    self.assertEqual(result, 123)

  def test_decode_int8(self):
    """Tests the decode_int8 method."""
    data = struct.pack("b", -123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeInt8()
    self.assertEqual(offset, 0)
    self.assertEqual(result, -123)

  def test_decode_int16(self):
    """Tests the decode_int16 method."""
    data = struct.pack("<h", -123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeInt16()
    self.assertEqual(offset, 0)
    self.assertEqual(result, -123)

  def test_decode_int24(self):
    """Tests the decode_int24 method."""
    data = struct.pack("<i", -123)[:3]
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeInt24()
    self.assertEqual(offset, 0)
    self.assertEqual(result, -123)

  def test_decode_int32(self):
    """Tests the decode_int32 method."""
    data = struct.pack("<i", -123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeInt32()
    self.assertEqual(offset, 0)
    self.assertEqual(result, -123)

  def test_decode_int48(self):
    """Tests the decode_int48 method."""
    data = struct.pack("<q", -123)[:6]
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeInt48()
    self.assertEqual(offset, 0)
    self.assertEqual(result, -123)

  def test_decode_int64(self):
    """Tests the decode_int64 method."""
    data = struct.pack("<q", -123)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeInt64()
    self.assertEqual(offset, 0)
    self.assertEqual(result, -123)

  def test_decode_double(self):
    """Tests the decode_double method."""
    data = struct.pack("<d", 3.14)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeDouble()
    self.assertEqual(offset, 0)
    self.assertAlmostEqual(result, 3.14, places=3)

  def test_decode_float(self):
    """Tests the decode_float method."""
    data = struct.pack("<f", 3.14)
    stream = io.BytesIO(data)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeFloat()
    self.assertEqual(offset, 0)
    self.assertAlmostEqual(result, 3.14, places=3)

  def test_decode_varint(self):
    """Tests the decode_varint method."""
    varint_bytes = b"\x80\x80\x01"
    expected_result = 16384
    stream = io.BytesIO(varint_bytes)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeVarint()
    self.assertEqual(offset, 0)
    self.assertEqual(result, expected_result)

  def test_decode_zigzag_varint(self):
    """Tests the decode_zigzag_varint method."""
    varint_bytes = b"\x80\x80\x01"
    expected_result = 8192
    stream = io.BytesIO(varint_bytes)
    decoder = utils.StreamDecoder(stream)
    offset, result = decoder.DecodeZigzagVarint()
    self.assertEqual(offset, 0)
    self.assertEqual(result, expected_result)


if __name__ == "__main__":
  unittest.main()
