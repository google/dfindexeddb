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
"""Unit tests for blink serialized objects."""
import unittest

from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.indexeddb.chromium import definitions


class BlinkTest(unittest.TestCase):
  """Unit tests for blink serialized objects."""

  def test_readcryptokey(self):
    """Tests Javascript CryptoKey decoding."""
    with self.subTest('AES'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x01, 0x01, 0x10, 0x04,
          0x10, 0x7e, 0x25, 0xb2, 0xe8, 0x62, 0x3e, 0xd7, 0x83,
          0x70, 0xa2, 0xae, 0x98, 0x79, 0x1b, 0xc5, 0xf7
      ]
      serialized_value = bytes(test_bytes)
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              'id': definitions.CryptoKeyAlgorithm.AES_CBC,
              'length_bits': 128
          },
          key_type=definitions.WebCryptoKeyType.SECRET,
          extractable=False,
          usages=definitions.CryptoKeyUsage.DECRYPT,
          key_data=b'~%\xb2\xe8b>\xd7\x83p\xa2\xae\x98y\x1b\xc5\xf7'
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('HMAC'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x02, 0x40, 0x06, 0x10, 0x40, 0xd9,
          0xbd, 0x0e, 0x84, 0x24, 0x3c, 0xb0, 0xbc, 0xee, 0x36, 0x61, 0xdc,
          0xd0, 0xb0, 0xf5, 0x62, 0x09, 0xab, 0x93, 0x8c, 0x21, 0xaf, 0xb7,
          0x66, 0xa9, 0xfc, 0xd2, 0xaa, 0xd8, 0xd4, 0x79, 0xf2, 0x55, 0x3a,
          0xef, 0x46, 0x03, 0xec, 0x64, 0x2f, 0x68, 0xea, 0x9f, 0x9d, 0x1d,
          0xd2, 0x42, 0xd0, 0x13, 0x6c, 0xe0, 0xe1, 0xed, 0x9c, 0x59, 0x46,
          0x85, 0xaf, 0x41, 0xc4, 0x6a, 0x2d, 0x06, 0x7a
      ]
      serialized_value = bytes(test_bytes)
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              'id': definitions.CryptoKeyAlgorithm.SHA256,
              'length_bits': 512
          },
          key_type=definitions.WebCryptoKeyType.SECRET,
          extractable=False,
          usages=definitions.CryptoKeyUsage.VERIFY,
          key_data=(
              b'\xd9\xbd\x0e\x84$<\xb0\xbc\xee6a\xdc\xd0\xb0\xf5b'
              b'\t\xab\x93\x8c!\xaf\xb7f\xa9\xfc\xd2\xaa\xd8\xd4y'
              b'\xf2U:\xefF\x03\xecd/h\xea\x9f\x9d\x1d\xd2B\xd0\x13'
              b'l\xe0\xe1\xed\x9cYF\x85\xafA\xc4j-\x06z'
          )
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('RSAHashedKey'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x04, 0x0d, 0x01, 0x80, 0x08, 0x03,
          0x01, 0x00, 0x01, 0x06, 0x11, 0xa2, 0x01, 0x30, 0x81, 0x9f, 0x30,
          0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01,
          0x01, 0x05, 0x00, 0x03, 0x81, 0x8d, 0x00, 0x30, 0x81, 0x89, 0x02,
          0x81, 0x81, 0x00, 0xae, 0xef, 0x7f, 0xee, 0x3a, 0x48, 0x48, 0xea,
          0xce, 0x18, 0x0b, 0x86, 0x34, 0x6c, 0x1d, 0xc5, 0xe8, 0xea, 0xab,
          0x33, 0xd0, 0x6f, 0x63, 0x82, 0x37, 0x18, 0x83, 0x01, 0x3d, 0x11,
          0xe3, 0x03, 0x79, 0x2c, 0x0a, 0x79, 0xe6, 0xf5, 0x14, 0x73, 0x5f,
          0x50, 0xa8, 0x17, 0x10, 0x58, 0x59, 0x20, 0x09, 0x54, 0x56, 0xe0,
          0x86, 0x07, 0x5f, 0xab, 0x9c, 0x86, 0xb1, 0x80, 0xcb, 0x72, 0x5e,
          0x55, 0x8b, 0x83, 0x98, 0xbf, 0xed, 0xbe, 0xdf, 0xdc, 0x6b, 0xff,
          0xcf, 0x50, 0xee, 0xcc, 0x7c, 0xb4, 0x8c, 0x68, 0x75, 0x66, 0xf2,
          0x21, 0x0d, 0xf5, 0x50, 0xdd, 0x06, 0x29, 0x57, 0xf7, 0x44, 0x42,
          0x3d, 0xd9, 0x30, 0xb0, 0x8a, 0x5e, 0x8f, 0xea, 0xff, 0x45, 0xa0,
          0x1d, 0x04, 0xbe, 0xc5, 0x82, 0xd3, 0x69, 0x4e, 0xcd, 0x14, 0x7b,
          0xf5, 0x00, 0x3c, 0xb1, 0x19, 0x24, 0xae, 0x8d, 0x22, 0xb5, 0x02,
          0x03, 0x01, 0x00, 0x01
      ]
      serialized_value = bytes(test_bytes)
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              'id': definitions.CryptoKeyAlgorithm.RSA_PSS,
              'modulus_length_bits': 1024,
              'public_exponent_size': 3,
              'public_exponent_bytes': b'\x01\x00\x01',
              'hash': definitions.CryptoKeyAlgorithm.SHA256
          },
          key_type=definitions.AsymmetricCryptoKeyType.PUBLIC_KEY,
          extractable=True,
          usages=(
              definitions.CryptoKeyUsage.VERIFY |
              definitions.CryptoKeyUsage.EXTRACTABLE
          ),
          key_data=(
              b'0\x81\x9f0\r\x06\t*\x86H\x86\xf7\r\x01\x01\x01\x05\x00\x03'
              b'\x81\x8d\x000\x81\x89\x02\x81\x81\x00\xae\xef\x7f\xee:HH\xea'
              b'\xce\x18\x0b\x864l\x1d\xc5\xe8\xea\xab3\xd0oc\x827\x18\x83'
              b'\x01=\x11\xe3\x03y,\ny\xe6\xf5\x14s_P\xa8\x17\x10XY \tTV\xe0'
              b'\x86\x07_\xab\x9c\x86\xb1\x80\xcbr^U\x8b\x83\x98\xbf\xed\xbe'
              b'\xdf\xdck\xff\xcfP\xee\xcc|\xb4\x8chuf\xf2!\r\xf5P\xdd\x06)W'
              b'\xf7DB=\xd90\xb0\x8a^\x8f\xea\xffE\xa0\x1d\x04\xbe\xc5\x82'
              b'\xd3iN\xcd\x14{\xf5\x00<\xb1\x19$\xae\x8d"\xb5\x02\x03\x01'
              b'\x00\x01'
          )
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('ECDSA Key'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x05, 0x0e, 0x01, 0x01, 0x11, 0x5b,
          0x30, 0x59, 0x30, 0x13, 0x06, 0x07, 0x2a, 0x86, 0x48, 0xce, 0x3d,
          0x02, 0x01, 0x06, 0x08, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01,
          0x07, 0x03, 0x42, 0x00, 0x04, 0xfe, 0x16, 0x70, 0x29, 0x07, 0x2c,
          0x11, 0xbf, 0xcf, 0xb7, 0x9d, 0x54, 0x35, 0x3d, 0xc7, 0x85, 0x66,
          0x26, 0xa5, 0xda, 0x69, 0x4c, 0x07, 0xd5, 0x74, 0xcb, 0x93, 0xf4,
          0xdb, 0x7e, 0x38, 0x3c, 0xa8, 0x98, 0x2a, 0x6f, 0xb2, 0xf5, 0x48,
          0x73, 0x2f, 0x59, 0x21, 0xa0, 0xa9, 0xf5, 0x6e, 0x37, 0x0c, 0xfc,
          0x5b, 0x68, 0x0e, 0x19, 0x5b, 0xd3, 0x4f, 0xb4, 0x0e, 0x1c, 0x31,
          0x5a, 0xaa, 0x2d
      ]
      serialized_value = bytes(test_bytes)
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              'crypto_key_algorithm': definitions.CryptoKeyAlgorithm.ECDSA,
              'named_curve_type': definitions.NamedCurve.P256
          },
          key_type=definitions.AsymmetricCryptoKeyType.PUBLIC_KEY,
          extractable=True,
          usages=(
              definitions.CryptoKeyUsage.VERIFY
              | definitions.CryptoKeyUsage.EXTRACTABLE
          ),
          key_data=(
              b'0Y0\x13\x06\x07*\x86H\xce=\x02\x01\x06\x08*\x86H\xce=\x03\x01'
              b'\x07\x03B\x00\x04\xfe\x16p)\x07,\x11\xbf\xcf\xb7\x9dT5=\xc7'
              b'\x85f&\xa5\xdaiL\x07\xd5t\xcb\x93\xf4\xdb~8<\xa8\x98*o\xb2'
              b'\xf5Hs/Y!\xa0\xa9\xf5n7\x0c\xfc[h\x0e\x19[\xd3O\xb4\x0e\x1c'
              b'1Z\xaa-'
          )
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('NoParams Key'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x06, 0x11, 0xa0, 0x02,
          0x03, 0x01, 0x02, 0x03, 0x00
      ]
      serialized_value = bytes(test_bytes)
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              'crypto_key_algorithm': definitions.CryptoKeyAlgorithm.PBKDF2
          },
          key_type=definitions.WebCryptoKeyType.SECRET,
          extractable=False,
          usages=(
              definitions.CryptoKeyUsage.DRIVE_BITS
              | definitions.CryptoKeyUsage.DERIVE_KEY
          ),
          key_data=b'\x01\x02\x03'
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMPoint(self):
    """Tests DOMPoint decoding."""
    test_bytes = [
        0xff, 0x11, 0xff, 0x0d, 0x5c, ord('Q'), 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xf0, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x40,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x40
    ]
    serialized_value = bytes(test_bytes)
    expected_value = blink.DOMPoint(x=1.0, y=2.0, z=3.0, w=4.0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)


if __name__ == '__main__':
  unittest.main()
