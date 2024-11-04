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
"""Unit tests for Webkit encoded JavaScript values."""
import datetime
import unittest

from dfindexeddb.indexeddb import types
from dfindexeddb.indexeddb.safari import definitions
from dfindexeddb.indexeddb.safari import webkit


class WebkitTest(unittest.TestCase):
  """Unit tests for Webkit encoded JavaScript values."""

  def test_parse_undefined(self):
    """Tests parsing an undefined value from an IndexedDB value."""
    expected_value = {'id': 10, 'value': types.Undefined()}
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050A0000000500008076616C756503FFFFFFFF')
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_null(self):
    """Tests parsing a null value from an IndexedDB value."""
    expected_value = {'id': 11, 'value': types.Null()}
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050B0000000500008076616C756504FFFFFFFF')
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_zero(self):
    """Tests parsing a zero value from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050C0000000500008076616C756506FFFFFFFF')
    expected_value = {'id': 12, 'value': 0}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_one(self):
    """Tests parsing a one value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050D0000000500008076616C756507FFFFFFFF')
    expected_value = {'id': 13, 'value': 1}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_integer(self):
    """Tests parsing an integer value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050E0000000500008076616C7565057B000000FFFF'
        'FFFF')
    expected_value = {'id': 14, 'value': 123}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_true(self):
    """Tests parsing a true value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050F0000000500008076616C756509FFFFFFFF')
    expected_value = {'id': 15, 'value': True}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_false(self):
    """Tests parsing a false value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405100000000500008076616C756508FFFFFFFF')
    expected_value = {'id': 16, 'value': False}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_true_object(self):
    """Tests parsing a true object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405110000000500008076616C756518FFFFFFFF')
    expected_value = {'id': 17, 'value': True}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_false_object(self):
    """Tests parsing a false object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405120000000500008076616C756519FFFFFFFF')
    expected_value = {'id': 18, 'value': False}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_number(self):
    """Tests parsing a number from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405130000000500008076616C75650A1F85EB51B81E'
        '0940FFFFFFFF')
    expected_value = {'id': 19, 'value': 3.14}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_number_object(self):
    """Tests parsing a number object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405140000000500008076616C75651C1F85EB51B81E'
        '0940FFFFFFFF')
    expected_value = {'id': 20, 'value': 3.14}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_bigint(self):
    """Tests parsing a bigint from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405150000000500008076616C75652F000200000000'
        '00C098CE3FCAC89A02000000000000FFFFFFFF')
    # BigInt(123e20) === 12300000000000001048576n
    expected_value = {'id': 21, 'value': 12300000000000001048576}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_date(self):
    """Tests parsing a date from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405160000000500008076616C75650B00803FE17E64'
        '7842FFFFFFFF')
    # Date(2023, 1, 13, 10, 20, 30, 456)
    # note JavaScript dates, month is 0-indexed and the date is in localtime
    # (UTC+11)
    expected_value = {
        'id': 22,
        'value': datetime.datetime(
            year=2023, month=2, day=12, hour=23, minute=20, second=30,
            microsecond=456000)}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_string(self):
    """Tests parsing a string from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405170000000500008076616C756510110000807465'
        '737420737472696E672076616C7565FFFFFFFF')
    expected_value = {'id': 23, 'value': 'test string value'}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_string_object(self):
    """Tests parsing a string object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405180000000500008076616C75651A120000807465'
        '737420737472696E67206F626A656374FFFFFFFF')
    expected_value = {'id': 24, 'value': 'test string object'}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_string(self):
    """Tests parsing an empty string from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F0000000202000080696405190000000500008076616C756511FFFFFFFF')
    expected_value = {'id': 25, 'value': ''}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_string_object(self):
    """Tests parsing an empty string object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964051A0000000500008076616C75651BFFFFFFFF')
    expected_value = {'id': 26, 'value': ''}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_set(self):
    """Tests parsing a set from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964051B0000000500008076616C75651D070502000000'
        '050300000020FFFFFFFFFFFFFFFF')
    expected_set = types.JSSet()
    for i in range(1, 4):
      expected_set.values.add(i)
    expected_value = {'id': 27, 'value': expected_set}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_map(self):
    """Tests parsing a map from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964051C0000000500008076616C75651E1FFFFFFFFFFFFF'
        'FFFF')
    expected_value = {'id': 28, 'value': {}}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_regexp(self):
    """Tests parsing a regexp from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964051D0000000500008076616C75651200000080FEFF'
        'FFFF02FFFFFFFF')
    expected_value = {'id': 29, 'value': types.RegExp(pattern='', flags='')}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_object(self):
    """Tests parsing a empty object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964051E0000000500008076616C756502FFFFFFFFFFFF'
        'FFFF')
    expected_value = {'id': 30, 'value': {}}
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_mixed_object(self):
    """Tests parsing a object with mixed values from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964070A000080746573745F756E646566030900008074'
        '6573745F6E756C6C040E000080746573745F626F6F6C5F74727565090F000080'
        '746573745F626F6F6C5F66616C7365080B000080746573745F737472696E6710'
        '0E0000806120737472696E672076616C75650B000080746573745F6E756D6265'
        '720A1F85EB51B81E094012000080746573745F737472696E675F6F626A656374'
        '1A0F0000806120737472696E67206F626A65637412000080746573745F6E756D'
        '6265725F6F626A6563741C1F85EB51B81E094018000080746573745F626F6F6C'
        '65616E5F747275655F6F626A6563741819000080746573745F626F6F6C65616E'
        '5F66616C73655F6F626A656374190B000080746573745F626967696E742F0002'
        '0000000000C098CE3FCAC89A0200000000000009000080746573745F64617465'
        '0B00803FE17E64784208000080746573745F7365741D07050200000005030000'
        '0020FFFFFFFF08000080746573745F6D61701E10010000806107100100008062'
        '050200000010010000806305030000001FFFFFFFFF0B000080746573745F7265'
        '6765787012030000805C772B000000800A000080746573745F61727261790104'
        '00000000000000057B0000000100000005C80100000200000010030000806162'
        '63030000001003000080646566FFFFFFFFFFFFFFFF0B000080746573745F6F62'
        '6A65637402040000806E616D650205000080666972737410040000804A616E65'
        '040000806C6173741003000080446F65FFFFFFFF030000806167650515000000'
        'FFFFFFFFFFFFFFFF')

    expected_test_array = types.JSArray()
    for value in [123, 456, 'abc', 'def']:
      expected_test_array.values.append(value)
    expected_set = types.JSSet()
    for i in range(1, 4):
      expected_set.values.add(i)

    expected_value = {
       'id': 1,
        'test_undef': types.Undefined(),
        'test_null': types.Null(),
        'test_bool_true': True,
        'test_bool_false': False,
        'test_string': 'a string value',
        'test_number': 3.14,
        'test_string_object': 'a string object',
        'test_number_object': 3.14,
        'test_boolean_true_object': True,
        'test_boolean_false_object': False,
        'test_bigint': 12300000000000001048576,
        'test_date': datetime.datetime(2023, 2, 12, 23, 20, 30, 456000),
        'test_set': expected_set,
        'test_map': {
            'a': 1,
            'b': 2,
            'c': 3},
        'test_regexp': types.RegExp('\\w+', ''),
        'test_array': expected_test_array,
        'test_object': {
            'name': {
                'first': 'Jane',
                'last': 'Doe'
            },
            'age': 21,
        }
    }
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_nested_array(self):
    """Tests parsing a nested array value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        '0F00000002020000806964050200000009000080746573745F646174650B0090'
        '3FE17E64784211000080746573745F6E65737465645F61727261790208000080'
        '6C6576656C5F696407050000806368696C6402FEFFFFFF030502000000FEFFFF'
        'FF0402FEFFFFFF030503000000FEFFFFFF0402FEFFFFFF030504000000FEFFFF'
        'FF0402FEFFFFFF030505000000FEFFFFFF0402FEFFFFFF030506000000FEFFFF'
        'FF0402FEFFFFFF030507000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        'FFFFFFFFFFFFFFFFFFFFFFFFFF')
    expected_value = {
        'id': 2,
        'test_date': datetime.datetime(2023, 2, 12, 23, 20, 30, 457000),
        'test_nested_array': {
            'level_id': 1,
            'child': {
                'level_id': 2,
                'child': {
                    'level_id': 3,
                    'child': {
                        'level_id': 4,
                        'child': {
                            'level_id': 5,
                            'child': {
                                'level_id': 6,
                                'child': {
                                    'level_id': 7
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    parsed_value = webkit.SerializedScriptValueDecoder.FromBytes(
        value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_date_key(self):
    """Tests parsing a date from an IDB key."""
    expected_key = webkit.IDBKeyData(
        offset=0,
        key_type=definitions.SIDBKeyType.DATE,
        data=datetime.datetime(2023, 2, 12, 23, 20, 30, 456000))
    key_bytes = bytes.fromhex('004000803FE17E647842')
    parsed_key = webkit.IDBKeyData.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_number_key(self):
    """Tests parsing a number from an IDB key."""
    expected_key = webkit.IDBKeyData(
        offset=0,
        key_type=definitions.SIDBKeyType.NUMBER,
        data=-3.14)
    key_bytes = bytes.fromhex('00201F85EB51B81E09C0')
    parsed_key = webkit.IDBKeyData.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_string_key(self):
    """Tests parsing a number from an IDB key."""
    expected_key = webkit.IDBKeyData(
        offset=0,
        key_type=definitions.SIDBKeyType.STRING,
        data='test string key')
    key_bytes = bytes.fromhex(
        '00600F0000007400650073007400200073007400720069006E00670020006B00'
        '65007900')
    parsed_key = webkit.IDBKeyData.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_uintarray_key(self):
    """Tests parsing a number from an IDB key."""
    expected_key = webkit.IDBKeyData(
        offset=0,
        key_type=definitions.SIDBKeyType.BINARY,
        data=b'\x00\x00\x00')
    key_bytes = bytes.fromhex('00800300000000000000000000')
    parsed_key = webkit.IDBKeyData.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_array_key(self):
    """Tests parsing an array from an IDB key."""
    expected_key = webkit.IDBKeyData(
        offset=0,
        key_type=definitions.SIDBKeyType.ARRAY,
        data=[1, 2, 3])
    key_bytes = bytes.fromhex(
        '00A0030000000000000020000000000000F03F20000000000000004020000000'
        '0000000840')
    parsed_key = webkit.IDBKeyData.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)


if __name__ == '__main__':
  unittest.main()
