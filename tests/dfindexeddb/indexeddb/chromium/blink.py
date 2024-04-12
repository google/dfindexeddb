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

  def test_ReadCryptoKey(self):
    """Tests Javascript CryptoKey decoding."""
    with self.subTest('AES'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x01, 0x01, 0x10,
          0x04, 0x10,
          0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,  # key data
          0x08, 0x09, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15
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
        key_data=(
              b'\x00\x01\x02\x03\x04\x05\x06\x07'
              b'\x08\x09\x10\x11\x12\x13\x14\x15')
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('HMAC'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x02, 0x40, 0x06,
          0x10, 0x40,
          0x84, 0x04, 0x10, 0xb5, 0xb3, 0x15, 0xec, 0x95,  # key data
          0x4c, 0x3b, 0xc7, 0x9c, 0x6a, 0x89, 0x06, 0xaa,
          0x25, 0x9a, 0xfe, 0xeb, 0x30, 0x14, 0xfa, 0x81,
          0x95, 0xd2, 0x69, 0x48, 0x87, 0xe8, 0x60, 0x2c,
          0x89, 0xb3, 0x22, 0xfd, 0x6a, 0x74, 0xe2, 0xdc,
          0x60, 0xbd, 0xd1, 0xcd, 0x2e, 0x2f, 0x1f, 0xb6,
          0x7f, 0xf6, 0x22, 0xf1, 0x25, 0xe8, 0xd7, 0x90,
          0xfb, 0x80, 0x21, 0x7e, 0x79, 0xc3, 0x5f, 0x98
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
              b'\x84\x04\x10\xb5\xb3\x15\xec\x95'
              b'\x4c\x3b\xc7\x9c\x6a\x89\x06\xaa'
              b'\x25\x9a\xfe\xeb\x30\x14\xfa\x81'
              b'\x95\xd2\x69\x48\x87\xe8\x60\x2c'
              b'\x89\xb3\x22\xfd\x6a\x74\xe2\xdc'
              b'\x60\xbd\xd1\xcd\x2e\x2f\x1f\xb6'
              b'\x7f\xf6\x22\xf1\x25\xe8\xd7\x90'
              b'\xfb\x80\x21\x7e\x79\xc3\x5f\x98'
          )
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('RSAHashedKey'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x04, 0x0d, 0x01, 0x80, 0x08, 0x03,
          0x01, 0x00, 0x01, 0x06, 0x11, 0xa2, 0x01,
          0x0a, 0xc9, 0x9b, 0xea, 0x4a, 0x34, 0xec, 0x34,  # key data
          0xe0, 0x79, 0x5e, 0x8d, 0x12, 0x25, 0x4f, 0x19,
          0x93, 0x82, 0x32, 0xd8, 0x87, 0x60, 0xe7, 0x1d,
          0x9c, 0xe5, 0x42, 0x49, 0x28, 0x26, 0x45, 0x72,
          0x9d, 0x69, 0x86, 0x23, 0xd2, 0xa7, 0x51, 0x97,
          0xb8, 0x06, 0x9c, 0xb2, 0x03, 0xe3, 0xb8, 0xdc,
          0xab, 0x5f, 0xb4, 0xc1, 0x2b, 0xc2, 0xd5, 0x37,
          0x12, 0x3d, 0x25, 0x1a, 0xfb, 0x42, 0x6d, 0xd6,
          0x51, 0xb3, 0x64, 0xbf, 0x50, 0xaf, 0x31, 0x25,
          0xcb, 0x98, 0x1a, 0xb7, 0xac, 0x67, 0x86, 0x68,
          0xf1, 0x4c, 0xcc, 0x34, 0x28, 0xa6, 0xc9, 0x9a,
          0x3e, 0x5c, 0x75, 0x61, 0xa1, 0x78, 0x39, 0x6e,
          0x4e, 0x10, 0x48, 0xf8, 0x5e, 0x69, 0xf1, 0xb4,
          0x3c, 0x12, 0x11, 0x63, 0x68, 0x7b, 0x86, 0xd8,
          0xa8, 0xe3, 0x83, 0xf9, 0x3f, 0xa0, 0xc6, 0xfb,
          0x0d, 0x5a, 0x01, 0x82, 0x9b, 0x9e, 0x7a, 0xa4,
          0x57, 0xa3, 0x84, 0x2b, 0xb6, 0xc7, 0xae, 0x0e,
          0xad, 0xeb, 0x86, 0xc8, 0x72, 0xb3, 0x2a, 0x5e,
          0xf3, 0x1a, 0x33, 0x59, 0xe3, 0x61, 0xba, 0x91,
          0x85, 0xf8, 0x48, 0x3b, 0x9a, 0xb6, 0xbf, 0xe9,
          0xe3, 0xb3
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
              b'\x0a\xc9\x9b\xea\x4a\x34\xec\x34'
              b'\xe0\x79\x5e\x8d\x12\x25\x4f\x19'
              b'\x93\x82\x32\xd8\x87\x60\xe7\x1d'
              b'\x9c\xe5\x42\x49\x28\x26\x45\x72'
              b'\x9d\x69\x86\x23\xd2\xa7\x51\x97'
              b'\xb8\x06\x9c\xb2\x03\xe3\xb8\xdc'
              b'\xab\x5f\xb4\xc1\x2b\xc2\xd5\x37'
              b'\x12\x3d\x25\x1a\xfb\x42\x6d\xd6'
              b'\x51\xb3\x64\xbf\x50\xaf\x31\x25'
              b'\xcb\x98\x1a\xb7\xac\x67\x86\x68'
              b'\xf1\x4c\xcc\x34\x28\xa6\xc9\x9a'
              b'\x3e\x5c\x75\x61\xa1\x78\x39\x6e'
              b'\x4e\x10\x48\xf8\x5e\x69\xf1\xb4'
              b'\x3c\x12\x11\x63\x68\x7b\x86\xd8'
              b'\xa8\xe3\x83\xf9\x3f\xa0\xc6\xfb'
              b'\x0d\x5a\x01\x82\x9b\x9e\x7a\xa4'
              b'\x57\xa3\x84\x2b\xb6\xc7\xae\x0e'
              b'\xad\xeb\x86\xc8\x72\xb3\x2a\x5e'
              b'\xf3\x1a\x33\x59\xe3\x61\xba\x91'
              b'\x85\xf8\x48\x3b\x9a\xb6\xbf\xe9'
              b'\xe3\xb3'
          )
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest('ECDSA Key'):
      test_bytes = [
          0xff, 0x09, 0x3f, 0x00, 0x4b, 0x05, 0x0e, 0x01, 0x01, 0x11, 0x5b,
          0xcb, 0x98, 0x1a, 0xb7, 0xac, 0x67, 0x86, 0x68,  # key data
          0xf1, 0x4c, 0xcc, 0x34, 0x28, 0xa6, 0xc9, 0x9a,
          0x3e, 0x5c, 0x75, 0x61, 0xa1, 0x78, 0x39, 0x6e,
          0x4e, 0x10, 0x48, 0xf8, 0x5e, 0x69, 0xf1, 0xb4,
          0x3c, 0x12, 0x11, 0x63, 0x68, 0x7b, 0x86, 0xd8,
          0xa8, 0xe3, 0x83, 0xf9, 0x3f, 0xa0, 0xc6, 0xfb,
          0x0d, 0x5a, 0x01, 0x82, 0x9b, 0x9e, 0x7a, 0xa4,
          0x57, 0xa3, 0x84, 0x2b, 0xb6, 0xc7, 0xae, 0x0e,
          0xad, 0xeb, 0x86, 0xc8, 0x72, 0xb3, 0x2a, 0x5e,
          0xf3, 0x1a, 0x33, 0x59, 0xe3, 0x61, 0xba, 0x91,
          0x85, 0xf8, 0x48, 0x3b, 0x9a, 0xb6, 0xbf, 0xe9,
          0xe3, 0xb3, 0x30
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
              b'\xcb\x98\x1a\xb7\xac\x67\x86\x68'
              b'\xf1\x4c\xcc\x34\x28\xa6\xc9\x9a'
              b'\x3e\x5c\x75\x61\xa1\x78\x39\x6e'
              b'\x4e\x10\x48\xf8\x5e\x69\xf1\xb4'
              b'\x3c\x12\x11\x63\x68\x7b\x86\xd8'
              b'\xa8\xe3\x83\xf9\x3f\xa0\xc6\xfb'
              b'\x0d\x5a\x01\x82\x9b\x9e\x7a\xa4'
              b'\x57\xa3\x84\x2b\xb6\xc7\xae\x0e'
              b'\xad\xeb\x86\xc8\x72\xb3\x2a\x5e'
              b'\xf3\x1a\x33\x59\xe3\x61\xba\x91'
              b'\x85\xf8\x48\x3b\x9a\xb6\xbf\xe9'
              b'\xe3\xb3\x30'
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


if __name__ == '__main__':
  unittest.main()
