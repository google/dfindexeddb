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
"""Unit tests for Gecko encoded JavaScript values."""
import datetime
import unittest

from dfindexeddb.indexeddb import types
from dfindexeddb.indexeddb.firefox import definitions, gecko


class GeckoTest(unittest.TestCase):
  """Unit tests for Gecko encoded JavaScript values."""

  def test_parse_undefined(self) -> None:
    """Tests parsing an undefined value from an IndexedDB value."""
    expected_value = {"id": 10, "value": types.Undefined()}
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800000A"
        "0000000300FFFF050D181476616C75650009012C0100FFFF000000001300FFFF"
    )
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_null(self) -> None:
    """Tests parsing a null value from an IndexedDB value."""
    expected_value = {"id": 11, "value": types.Null()}
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800000B"
        "0000000300FFFF050D181076616C7565091B30000000FFFF000000001300FFFF"
    )
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_zero(self) -> None:
    """Tests parsing a zero value from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800000C"
        "0000000300FFFF050D181476616C75650009012C0300FFFF000000001300FFFF"
    )
    expected_value = {"id": 12, "value": 0}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_one(self) -> None:
    """Tests parsing a one value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800000D"
        "0000000300FFFF050D185C76616C7565000000010000000300FFFF0000000013"
        "00FFFF"
    )
    expected_value = {"id": 13, "value": 1}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_integer(self) -> None:
    """Tests parsing an integer value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800000E"
        "0000000300FFFF050D185C76616C75650000007B0000000300FFFF0000000013"
        "00FFFF"
    )
    expected_value = {"id": 14, "value": 123}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_true(self) -> None:
    """Tests parsing a true value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800000F"
        "0000000300FFFF050D185C76616C7565000000010000000200FFFF0000000013"
        "00FFFF"
    )
    expected_value = {"id": 15, "value": True}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_false(self) -> None:
    """Tests parsing a false value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800001"
        "00000000300FFFF050D181476616C75650009012C0200FFFF000000001300FF"
        "FF"
    )
    expected_value = {"id": 16, "value": False}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_true_object(self) -> None:
    """Tests parsing a true object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF6964011228000011"
        "0000000300FFFF050D185C76616C7565000000010000000A00FFFF0000000013"
        "00FFFF"
    )
    expected_value = {"id": 17, "value": True}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_false_object(self) -> None:
    """Tests parsing a false object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF6964011228000012"
        "0000000300FFFF050D181476616C75650009012C0A00FFFF000000001300FFFF"
    )
    expected_value = {"id": 18, "value": False}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_number(self) -> None:
    """Tests parsing a number from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF6964011228000013"
        "0000000300FFFF050D185C76616C75650000001F85EB51B81E09400000000013"
        "00FFFF"
    )
    expected_value = {"id": 19, "value": 3.14}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_number_object(self) -> None:
    """Tests parsing a number object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "50040300010104F1FF0106340800FFFF020000800400FFFF6964011228000014"
        "0000000300FFFF050D181476616C75650009014C0C00FFFF1F85EB51B81E0940"
        "000000001300FFFF"
    )
    expected_value = {"id": 20, "value": 3.14}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_bigint(self) -> None:
    """Tests parsing a bigint from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "58040300010104F1FF0106340800FFFF020000800400FFFF696401122C000015"
        "0000000300FFFF050009189C76616C7565000000020000001D00FFFF0000C098"
        "CE3FCAC89A02000000000000000000001300FFFF"
    )
    # BigInt(123e20) === 12300000000000001048576n
    expected_value = {"id": 21, "value": 12300000000000001048576}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_date(self) -> None:
    """Tests parsing a date from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "50040300010104F1FF0106340800FFFF020000800400FFFF6964011228000016"
        "0000000300FFFF050D181476616C75650009014C0500FFFF00803FE17E647842"
        "000000001300FFFF"
    )
    # Date(2023, 1, 13, 10, 20, 30, 456)
    # note JavaScript dates, month is 0-indexed and the date is in localtime
    # (UTC+11)
    expected_value = {
        "id": 22,
        "value": datetime.datetime(
            year=2023,
            month=2,
            day=12,
            hour=23,
            minute=20,
            second=30,
            microsecond=456000,
            tzinfo=datetime.timezone.utc,
        ),
    }
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_string(self) -> None:
    """Tests parsing a string from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "60040300010104F1FF0106340800FFFF020000800400FFFF6964011228000017"
        "0000000300FFFF050D182076616C7565000000110D1030746573742073747269"
        "6E6720760D1C2C00000000000000001300FFFF"
    )
    expected_value = {"id": 23, "value": "test string value"}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_string_object(self) -> None:
    """Tests parsing a string object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "60040300010104F1FF0106340800FFFF020000800400FFFF6964011228000018"
        "0000000300FFFF050D18BC76616C7565000000120000800B00FFFF7465737420"
        "737472696E67206F626A656374000000000000000000001300FFFF"
    )
    expected_value = {"id": 24, "value": "test string object"}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_string(self) -> None:
    """Tests parsing an empty string from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF6964011228000019"
        "0000000300FFFF050D181076616C7565091B30800400FFFF000000001300FFFF"
    )
    expected_value = {"id": 25, "value": ""}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_string_object(self) -> None:
    """Tests parsing an empty string object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "48040300010104F1FF0106340800FFFF020000800400FFFF696401122800001A"
        "0000000300FFFF050D181476616C756500050130800B00FFFF000000001300FF"
        "FF"
    )
    expected_value = {"id": 26, "value": ""}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_set(self) -> None:
    """Tests parsing a set from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "68040300010104F1FF0106340800FFFF020000800400FFFF696401122800001B"
        "0000000300FFFF050D181076616C7565091B14001200FFFF010D2000020D0801"
        "50013001232C1300FFFF000000001300FFFF"
    )
    expected_set = types.JSSet()
    for i in range(1, 4):
      expected_set.values.add(i)
    expected_value = {"id": 27, "value": expected_set}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_map(self) -> None:
    """Tests parsing a map from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "50040300010104F1FF0106340800FFFF020000800400FFFF696401122800001C"
        "0000000300FFFF050D181476616C7565000901081100FF05382C1300FFFF0000"
        "00001300FFFF"
    )
    expected_value = {"id": 28, "value": {}}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_regexp(self) -> None:
    """Tests parsing a regexp from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "50040300010104F1FF0106340800FFFF020000800400FFFF696401122800001D"
        "0000000300FFFF050D181476616C7565000901080600FF013830800400FFFF00"
        "0000001300FFFF"
    )
    expected_value = {"id": 29, "value": types.RegExp(pattern="", flags="0")}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_empty_object(self) -> None:
    """Tests parsing a empty object from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "50040300010104F1FF0106340800FFFF020000800400FFFF696401122800001E"
        "0000000300FFFF050D181476616C75650009010130010A2C1300FFFF00000000"
        "1300FFFF"
    )
    expected_value = {"id": 30, "value": {}}
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_mixed_object(self) -> None:
    """Tests parsing a object with mixed values from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "8008040300010104F1FF0106340800FFFF020000800400FFFF69640112280000"
        "010000000300FFFF0A0D1824746573745F756E64656609200101100100FFFF09"
        "2E20000C6E756C6C0119150108FFFF0E2E200020626F6F6C5F74727565096010"
        "0200FFFF0F4220001066616C736505420120000B2E200014737472696E67051C"
        "115804612009150C2076616C0158323000146E756D6265720530201F85EB51B8"
        "1E094012465000185F6F626A656374052700000190080B00FF19580D1D323800"
        "095832380001010C0C00FFFF116800182E680001F80865616E05FB0D36200100"
        "00000A00FFFF194E280025030D2901590D01013032E00010626967696E092240"
        "020000001D00FFFF0000C098CE3FCAC89A01110800000032A0010C6461746501"
        "150D01000501301C803FE17E647842082E880004736505550C1200FFFF01A841"
        "08014F0108040300491801430C1300FFFF323800086D61700118001109384550"
        "00610111000029F0014000010D680062011504000005B82E1800006301150564"
        "36680032F800107265676578056B0501080600FF01980570085C772B051432B8"
        "021061727261790517180004000000070021280960007B0D0800010D0804C801"
        "09181DF00558046162099A00030D2800030DC82E1103211032A8004D3C110161"
        "6800040D38086E616D358B011800050D181466697273740005A80578084A616E"
        "05281138046C61051F0188052004446F051F050101801198046167091800150D"
        "B001212C1300FFFF000000001300FFFF"
    )

    expected_test_array = types.JSArray(values=[123, 456, "abc", "def"])
    expected_set = types.JSSet(values={1, 2, 3})

    expected_value = {
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
        "test_date": datetime.datetime(
            2023, 2, 12, 23, 20, 30, 456000, tzinfo=datetime.timezone.utc
        ),
        "test_set": expected_set,
        "test_map": {"a": 1, "b": 2, "c": 3},
        "test_regexp": types.RegExp("\\w+", "0"),
        "test_array": expected_test_array,
        "test_object": {
            "name": {"first": "Jane", "last": "Doe"},
            "age": 21,
        },
    }
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_nested_array(self) -> None:
    """Tests parsing a nested array value from an IndexedDB record."""
    value_bytes = bytes.fromhex(
        "F003040300010104F1FF0106340800FFFF020000800400FFFF69640112280000"
        "020000000300FFFF090D1820746573745F64617465091F0501300500FFFF0090"
        "3FE17E647842112E28002C6E65737465645F6172726179052A0901016800080D"
        "28206C6576656C5F6964010D6800050D180C6368696C0D8352300011989E3000"
        "0003BA60000004BA30000005BA30000006BA300000070D302142001321700400"
        "00D20800"
    )
    expected_value = {
        "id": 2,
        "test_date": datetime.datetime(
            2023, 2, 12, 23, 20, 30, 457000, tzinfo=datetime.timezone.utc
        ),
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
                            "child": {"level_id": 6, "child": {"level_id": 7}},
                        },
                    },
                },
            },
        },
    }
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_date_key(self) -> None:
    """Tests parsing a date from an IDB key."""
    expected_key = gecko.IDBKey(
        offset=0,
        type=definitions.IndexedDBKeyType.DATE,
        value=datetime.datetime(
            2023, 2, 12, 23, 20, 30, 456000, tzinfo=datetime.timezone.utc
        ),
    )
    key_bytes = bytes.fromhex("20C278647EE13F80")
    parsed_key = gecko.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_number_key(self) -> None:
    """Tests parsing a number from an IDB key."""
    expected_key = gecko.IDBKey(
        offset=0, type=definitions.IndexedDBKeyType.FLOAT, value=-3.14
    )
    key_bytes = bytes.fromhex("103FF6E147AE147AE1")
    parsed_key = gecko.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_string_key(self) -> None:
    """Tests parsing a number from an IDB key."""
    expected_key = gecko.IDBKey(
        offset=0,
        type=definitions.IndexedDBKeyType.STRING,
        value="test string key",
    )
    key_bytes = bytes.fromhex("3075667475217475736A6F68216C667A")
    parsed_key = gecko.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_uintarray_key(self) -> None:
    """Tests parsing a number from an IDB key."""
    expected_key = gecko.IDBKey(
        offset=0,
        type=definitions.IndexedDBKeyType.BINARY,
        value=b"\x00\x00\x00",
    )
    key_bytes = bytes.fromhex("40010101")
    parsed_key = gecko.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_array_key(self) -> None:
    """Tests parsing an array from an IDB key."""
    expected_key = gecko.IDBKey(
        offset=0, type=definitions.IndexedDBKeyType.ARRAY, value=[1, 2, 3]
    )
    key_bytes = bytes.fromhex("60BFF000000000000010C00000000000000010C008")
    parsed_key = gecko.IDBKey.FromBytes(key_bytes)
    self.assertEqual(parsed_key, expected_key)

  def test_parse_blob(self) -> None:
    """Tests parsing a blob from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "300000050128F1FF010000000180FFFF6405100800000A0D083C746578742F70"
        "6C61696E000000000000"
    )
    expected_value = gecko.Blob(index=1, size=100, type="text/plain")
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_file(self) -> None:
    """Tests parsing a file from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "480000050128f1ff020000000580ffffc80510080000090d0830696d6167652f"
        "706e6715cd5b0701140008010544000000746573742e706e6700000000000000"
    )
    expected_value = gecko.File(
        index=2,
        size=200,
        type="image/png",
        last_modified=123456789,
        name="test.png",
    )
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_urlsearchparams(self) -> None:
    """Tests parsing URLSearchParams from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "400000050104f1ff0107101480ffff0201090c0000000101050c000000611109"
        "00311109346201000000000000003200000000"
    )
    expected_value = gecko.URLSearchParams(params=[("a", "1"), ("b", "2")])
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_filelist(self) -> None:
    """Tests parsing FileList from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "480000050148f1ff010000000380ffff0580ffff030000002c01110c00000008"
        "010538000000746578742f637376b168de3a011011181c646174612e637376"
    )
    expected_value = gecko.FileList(
        files=[
            gecko.File(
                index=3,
                size=300,
                type="text/csv",
                last_modified=987654321,
                name="data.csv",
            )
        ]
    )
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_mutablefile(self) -> None:
    """Tests parsing a MutableFile from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "380000050104f1ff0107100480ffff0a010934000000746578742f706c61696e"
        "0b010f400000006d757461626c652e747874000000"
    )
    expected_value = gecko.MutableFile(name="mutable.txt", type="text/plain")
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_directory(self) -> None:
    """Tests parsing a Directory from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "280000050104f1ff0107102080ffff0c0109480000002f706174682f746f2f64"
        "697200000000"
    )
    expected_value = gecko.Directory(path="/path/to/dir")
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)

  def test_parse_wasm_module(self) -> None:
    """Tests parsing a WasmModule from an IndexedDB value."""
    value_bytes = bytes.fromhex(
        "180000050104f1ff01072c0680ffff7b000000c8010000"
    )
    expected_value = gecko.WasmModule(unused1=123, unused2=456)
    parsed_value = gecko.JSStructuredCloneDecoder.FromBytes(value_bytes)
    self.assertEqual(parsed_value, expected_value)


if __name__ == "__main__":
  unittest.main()
