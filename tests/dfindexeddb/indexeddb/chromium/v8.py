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
"""Unit tests for v8 serialized values."""
from datetime import datetime
import unittest

from dfindexeddb.indexeddb.chromium import definitions
from dfindexeddb.indexeddb.chromium import v8


class V8Test(unittest.TestCase):
  """Unit tests for v8 serialized values."""

  def test_oddballs(self):
    """Tests Javascript oddballs."""
    with self.subTest('undef'):
      # v8.serialize(undefined)
      buffer = b'\xff\x0d\x5f'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertIsInstance(parsed_value, v8.Undefined)

    with self.subTest('None'):
      # v8.serialize(null)
      buffer = b'\xff\x0d\x30'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertIsInstance(parsed_value, v8.Null)

    with self.subTest('true'):
      # v8.serialize(True)
      buffer = b'\xff\x0d\x54'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, True)

    with self.subTest('false'):
      # v8.serialize(False)
      buffer = b'\xff\x0d\x46'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, False)

  def test_int(self):
    """Tests int decoding."""

    with self.subTest('positive'):
      # v8.serialize(1234)
      buffer = b'\xff\x0d\x49\xa4\x13'
      expected_value = 1234
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('negative'):
      # v8.serialize(-1234)
      buffer = b'\xff\x0d\x49\xa3\x13'
      expected_value = -1234
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_double(self):
    """Tests double decoding."""

    with self.subTest('positive'):
      # v8.serialize(1234.456)
      buffer = b'\xff\x0d\x4e\xe7\xfb\xa9\xf1\xd2\x49\x93\x40'
      expected_value = 1234.456
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('negative'):
      # v8.serialize(-1234.456)
      buffer = b'\xff\x0d\x4e\xe7\xfb\xa9\xf1\xd2\x49\x93\xc0'
      expected_value = -1234.456
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_string(self):
    """Tests string decoding."""

    with self.subTest('ascii'):
      # console.log(v8.serialize('hello world').toString('hex'))
      buffer = bytes.fromhex('ff0d220b68656c6c6f20776f726c64')
      expected_value = 'hello world'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('emoji'):
      # console.log(v8.serialize('😄').toString('hex'))
      buffer = bytes.fromhex('ff0d63043dd804de')
      expected_value = '😄'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_bigint(self):
    """Tests bigint decoding."""

    with self.subTest('positive'):
      # console.log(v8.serialize(BigInt(1)).toString('hex'))
      buffer = bytes.fromhex('ff0d5a100100000000000000')
      expected_value = 1
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('large positive'):
      # console.log(v8.serialize(BigInt(123456789123456789n)).toString('hex'))
      buffer = bytes.fromhex('ff0d5a10155fd0ac4b9bb601')
      expected_value = 123456789123456789
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('negative'):
      # console.log(v8.serialize(BigInt(-1)).toString('hex'))
      buffer = bytes.fromhex('ff0d5a110100000000000000')
      expected_value = -1
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('large negative'):
      # console.log(v8.serialize(BigInt(-123456789123456789n)).toString('hex'))
      buffer = bytes.fromhex('ff0d5a11155fd0ac4b9bb601')
      expected_value = -123456789123456789
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_jsobject(self):
    """Tests object decoding."""

    with self.subTest('empty'):
      # console.log(v8.serialize(Object.create(null)).toString('hex'))
      buffer = bytes.fromhex('ff0d6f7b00')
      expected_value = {}
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('one property'):
      # onsole.log(v8.serialize(new Object({'propa': 123})).toString('hex'))
      buffer = bytes.fromhex('ff0d6f220570726f706149f6017b01')
      expected_value = {'propa': 123}
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_jsarray(self):
    """Tests array decoding."""

    with self.subTest('empty'):
      # console.log(v8.serialize([]).toString('hex'))
      buffer = bytes.fromhex('ff0d4100240000')
      expected_value = v8.JSArray()
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('one prop'):
      # > x = [1, 2, 3]
      # > x['propa'] = 123
      # > console.log(v8.serialize(x)).toString('hex'))
      buffer = bytes.fromhex('ff0d4103490249044906220570726f706149f601240103')
      expected_value = v8.JSArray()
      expected_value.Append(1)
      expected_value.Append(2)
      expected_value.Append(3)
      expected_value.properties['propa'] = 123
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)
      self.assertTrue(hasattr(parsed_value, 'propa'))
      self.assertEqual(parsed_value.properties['propa'], 123)

    with self.subTest('increase length'):
      # > x = new Array()
      # > x.length = 10
      # > console.log(v8.serialize(x)).toString('hex'))
      buffer = bytes.fromhex('ff0d610a40000a')
      expected_value = v8.JSArray()
      for _ in range(10):
        expected_value.Append(v8.Undefined())
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_jsmap(self):
    """Tests map decoding."""

    with self.subTest('empty'):
      # console.log(v8.serialize(new Map()).toString('hex'))
      buffer = bytes.fromhex('ff0d3b3a00')
      expected_value = {}
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('two keys'):
      # console.log(
      #     v8.serialize(new Map([['a', 123], ['b', 456]])).toString('hex'))
      buffer = bytes.fromhex('ff0d3b22016149f6012201624990073a04')
      expected_value = {'a': 123, 'b': 456}
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_jsset(self):
    """Tests set decoding."""

    with self.subTest('empty'):
      # console.log(v8.serialize(new Set()).toString('hex'))
      buffer = bytes.fromhex('ff0d272c00')
      expected_value = set()
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('3 entries'):
      # console.log(v8.serialize(new Set([1, 2, 3, 3])).toString('hex'))
      buffer = bytes.fromhex('ff0d274902490449062c03')
      expected_value = set([1, 2, 3])
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_arraybuffer(self):
    """Tests ArrayBuffer decoding."""

    with self.subTest('empty'):
      # console.log(v8.serialize(new ArrayBuffer()).toString('hex'))
      buffer = bytes.fromhex('ff0d4200')
      expected_value = b''
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('initialised'):
      # console.log(v8.serialize(new ArrayBuffer(8)).toString('hex'))
      buffer = bytes.fromhex('ff0d42080000000000000000')
      expected_value = b'\x00\x00\x00\x00\x00\x00\x00\x00'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_arraybufferview(self):
    """Tests ArrayBufferView decoding."""
    buffer = (
        b'\xff\x0dB\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00VB\x00\x10')
    expected_value = v8.BufferArrayView(
        buffer=(
            b'\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00'),
        flags=0,
        length=16,
        offset=0,
        tag=definitions.V8ArrayBufferViewTag.UINT8_ARRAY)
    parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
    self.assertEqual(parsed_value, expected_value)

  def test_date(self):
    """Tests date decoding."""
    # console.log(
    #     v8.serialize(new Date('1995-12-17T03:24:00Z')).toString('hex'))
    buffer = bytes.fromhex('ff0d44000010004cd76742')
    expected_value = datetime(1995, 12, 17, 3, 24)
    parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
    self.assertEqual(parsed_value, expected_value)

  def test_wrapped_primitives(self):
    """Tests wrapped primitive types."""

    with self.subTest('true'):
      # v8.serialize(new Boolean(True))
      buffer = b'\xff\x0d\x79'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, True)

    with self.subTest('false'):
      # v8.serialize(new Boolean(False))
      buffer = b'\xff\x0d\x78'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, False)

    with self.subTest('number'):
      # console.log(v8.serialize(new Number(-123456789)).toString('hex'))
      buffer = bytes.fromhex('ff0d6e00000054346f9dc1')
      expected_value = -123456789
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('bigint'):
      # console.log(
      #     v8.serialize(new Object(-123456789123456789n)).toString('hex'))
      buffer = bytes.fromhex('ff0d7a11155fd0ac4b9bb601')
      expected_value = -123456789123456789
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('string'):
      # console.log(v8.serialize(new String('hello world')).toString('hex'))
      buffer = bytes.fromhex('ff0d73220b68656c6c6f20776f726c64')
      expected_value = 'hello world'
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

  def test_regexp(self):
    """Test regexp decoding."""

    with self.subTest('empty'):
      # console.log(v8.serialize(new RegExp()).toString('hex'))
      # /(?:)/
      buffer = bytes.fromhex('ff0d522204283f3a2900')
      expected_value = v8.RegExp(pattern='(?:)', flags=0)
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('basic'):
      # console.log(v8.serialize(new RegExp('\\w+')).toString('hex'))
      buffer = bytes.fromhex('ff0d5222035c772b00')
      expected_value = v8.RegExp(pattern='\\w+', flags=0)
      parsed_value = v8.ValueDeserializer.FromBytes(buffer, None)
      self.assertEqual(parsed_value, expected_value)


if __name__ == '__main__':
  unittest.main()
