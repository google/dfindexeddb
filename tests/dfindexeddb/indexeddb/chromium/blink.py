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

from dfindexeddb.indexeddb.chromium import blink, definitions


class BlinkTest(unittest.TestCase):
  """Unit tests for blink serialized objects."""

  def test_ReadBlob(self) -> None:
    """Tests Blink Blob decoding."""
    serialized_value = bytes.fromhex("ff093f00620161016200")
    expected_value = blink.Blob(uuid="a", type="b", size=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadBlobIndex(self) -> None:
    """Tests Blink BlobIndex decoding."""
    serialized_value = bytes.fromhex("ff093f006900")
    expected_value = blink.BlobIndex(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadFile(self) -> None:
    """Tests Blink File decoding."""
    with self.subTest("file_v3"):
      serialized_value = bytes.fromhex(
          "ff033f0066047061746804757569640a746578742f706c61696e"
      )
      expected_value = blink.File(
          path="path",
          name=None,
          relative_path=None,
          uuid="uuid",
          type="text/plain",
          has_snapshot=0,
          size=None,
          last_modified_ms=None,
          is_user_visible=1,
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)
    with self.subTest("file_v4"):
      serialized_value = bytes.fromhex(
          "ff043f00660470617468046e616d650d72656c61746976655f70617468047575"
          "69640a746578742f706c61696e00"
      )
      expected_value = blink.File(
          path="path",
          name="name",
          relative_path="relative_path",
          uuid="uuid",
          type="text/plain",
          has_snapshot=0,
          size=None,
          last_modified_ms=None,
          is_user_visible=1,
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)
    with self.subTest("file_v8"):
      serialized_value = bytes.fromhex(
          "ff083f00660470617468046e616d650d72656c61746976655f70617468047575"
          "69640a746578742f706c61696e018004000000000000d0bf0100"
      )
      expected_value = blink.File(
          path="path",
          name="name",
          relative_path="relative_path",
          uuid="uuid",
          type="text/plain",
          has_snapshot=1,
          size=512,
          last_modified_ms=-0.25,
          is_user_visible=1,
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

  def test_ReadFileIndex(self) -> None:
    """Tests Blink FileIndex decoding."""
    serialized_value = bytes.fromhex("ff093f006500")
    expected_value = blink.FileIndex(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadFileList(self) -> None:
    """Tests Blink BlobIndex decoding."""
    serialized_value = bytes.fromhex(
        "ff033f006c0104706174680d72656c61746976655f706174680a746578742f70"
        "6c61696e"
    )
    parsed_file = blink.File(
        path="path",
        name=None,
        relative_path=None,
        uuid="relative_path",
        type="text/plain",
        has_snapshot=0,
        size=None,
        last_modified_ms=None,
        is_user_visible=1,
    )
    expected_value = blink.FileList(files=[parsed_file])
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadFileListIndex(self) -> None:
    """Tests Blink FileListIndex decoding."""
    serialized_value = bytes.fromhex("ff093f004c010000")
    expected_value = blink.FileListIndex(
        file_indexes=[blink.FileIndex(index=0)]
    )
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadImageBitmap(self) -> None:
    """Tests Blink ImageBitmap decoding."""
    with self.assertRaisesRegex(NotImplementedError, "ReadImageBitmap"):
      serialized_value = bytes.fromhex("ff093f006701010201080000ffff00ff00ff")
      _ = blink.V8ScriptValueDecoder.FromBytes(serialized_value)

  def test_ReadImageBitmapTransfer(self) -> None:
    """Tests Blink ImageBitmapTransfer decoding."""
    serialized_value = bytes.fromhex("ff093f004700")
    expected_value = blink.ImageBitmapTransfer(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadImageData(self) -> None:
    """Tests Blink ImageData decoding."""
    with self.assertRaisesRegex(NotImplementedError, "ReadImageData"):
      serialized_value = bytes.fromhex("ff093f002300")
      _ = blink.V8ScriptValueDecoder.FromBytes(serialized_value)

  def test_ReadDOMPoint(self) -> None:
    """Tests Blink DOMPoint decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c51000000000000f03f000000000000004000000000000008400000"
        "000000001040"
    )
    expected_value = blink.DOMPoint(x=1.0, y=2.0, z=3.0, w=4.0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMPointReadOnly(self) -> None:
    """Tests Blink DOMPointReadOnly decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c57000000000000f03f000000000000004000000000000008400000"
        "000000001040"
    )
    expected_value = blink.DOMPointReadOnly(x=1.0, y=2.0, z=3.0, w=4.0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMRect(self) -> None:
    """Tests Blink DOMRect decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c45000000000000f03f000000000000004000000000000008400000"
        "000000001040"
    )
    expected_value = blink.DOMRect(x=1.0, y=2.0, width=3.0, height=4.0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMRectReadOnly(self) -> None:
    """Tests Blink DOMReadReadOnly decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c52000000000000f03f000000000000004000000000000008400000"
        "000000001040"
    )
    expected_value = blink.DOMRectReadOnly(x=1.0, y=2.0, width=3.0, height=4.0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMQuad(self) -> None:
    """Tests Blink DOMQuad decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c54000000000000f03f000000000000144000000000000022400000"
        "000000002a400000000000000040000000000000184000000000000024400000"
        "000000002c4000000000000008400000000000001c4000000000000026400000"
        "000000002e400000000000001040000000000000204000000000000028400000"
        "000000003040"
    )
    expected_value = blink.DOMQuad(
        p1=blink.DOMPoint(x=1.0, y=5.0, z=9.0, w=13.0),
        p2=blink.DOMPoint(x=2.0, y=6.0, z=10.0, w=14.0),
        p3=blink.DOMPoint(x=3.0, y=7.0, z=11.0, w=15.0),
        p4=blink.DOMPoint(x=4.0, y=8.0, z=12.0, w=16.0),
    )
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMMatrix2D(self) -> None:
    """Tests Blink DOMMatrix2D decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c49000000000000f03f000000000000004000000000000008400000"
        "00000000104000000000000014400000000000001840ff11ff0d5c4900000000"
        "0000f03f00000000000000400000000000000840000000000000104000000000"
        "000014400000000000001840"
    )
    expected_value = blink.DOMMatrix2D(values=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMMatrix2DReadOnly(self) -> None:
    """Tests Blink DOMMatrix2DReadOnly decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c4f000000000000f03f000000000000004000000000000008400000"
        "00000000104000000000000014400000000000001840ff11ff0d5c4900000000"
        "0000f03f00000000000000400000000000000840000000000000104000000000"
        "000014400000000000001840"
    )
    expected_value = blink.DOMMatrix2DReadOnly(
        values=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    )
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMMatrix(self) -> None:
    """Tests Blink DOMMatrix decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c599a9999999999f13f333333333333f33fcdccccccccccf43f6666"
        "66666666f63fcdcccccccccc00409a9999999999014066666666666602403333"
        "333333330340cdcccccccccc08409a999999999909406666666666660a403333"
        "333333330b406666666666661040cdcccccccccc104033333333333311409a99"
        "999999991140"
    )
    expected_value = blink.DOMMatrix(
        values=[
            1.1,
            1.2,
            1.3,
            1.4,
            2.1,
            2.2,
            2.3,
            2.4,
            3.1,
            3.2,
            3.3,
            3.4,
            4.1,
            4.2,
            4.3,
            4.4,
        ]
    )
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMMatrixReadOnly(self) -> None:
    """Tests Blink DOMMatrixReadonly decoding."""
    serialized_value = bytes.fromhex(
        "ff11ff0d5c559a9999999999f13f333333333333f33fcdccccccccccf43f66666"
        "6666666f63fcdcccccccccc00409a999999999901406666666666660240333333"
        "3333330340cdcccccccccc08409a999999999909406666666666660a403333333"
        "333330b406666666666661040cdcccccccccc104033333333333311409a999999"
        "99991140"
    )
    expected_value = blink.DOMMatrixReadOnly(
        values=[
            1.1,
            1.2,
            1.3,
            1.4,
            2.1,
            2.2,
            2.3,
            2.4,
            3.1,
            3.2,
            3.3,
            3.4,
            4.1,
            4.2,
            4.3,
            4.4,
        ]
    )
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadMessagePort(self) -> None:
    """Tests Blink MessagePort decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c4d00")
    expected_value = blink.MessagePort(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadMojoHandle(self) -> None:
    """Tests Blink MojoHandle decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c6800")
    expected_value = blink.MojoHandle(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_OffscreenCanvasTransfer(self) -> None:
    """Tests Blink OffscreenCanvasTransfer decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c48000000000000")
    expected_value = blink.OffscreenCanvasTransfer(
        width=0, height=0, canvas_id=0, client_id=0, sink_id=0, filter_quality=0
    )
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadableStreamTransfer(self) -> None:
    """Tests Blink ReadableStreamTransfer decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c7200")
    expected_value = blink.ReadableStreamTransfer(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_WriteableStreamTransfer(self) -> None:
    """Tests Blink WriteableStreamTransfer decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c7700")
    expected_value = blink.WriteableStreamTransfer(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_TransformStreamTransfer(self) -> None:
    """Tests Blink TransformStreamTransfer decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c6d00")
    expected_value = blink.TransformStreamTransfer(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadDOMException(self) -> None:
    """Tests Blink DOMException decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c78014101420143")
    expected_value = blink.DOMException(name="A", message="B", stack_unused="C")
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadCryptoKey(self) -> None:
    """Tests Blink CryptoKey decoding."""
    with self.subTest("AES"):
      serialized_value = bytes.fromhex(
          "ff093f004b010110041000010203040506070809101112131415"
      )
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              "id": definitions.CryptoKeyAlgorithm.AES_CBC,
              "length_bits": 128,
          },
          key_type=definitions.WebCryptoKeyType.SECRET,
          extractable=False,
          usages=definitions.CryptoKeyUsage.DECRYPT,
          key_data=(
              b"\x00\x01\x02\x03\x04\x05\x06\x07"
              b"\x08\x09\x10\x11\x12\x13\x14\x15"
          ),
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("HMAC"):
      serialized_value = bytes.fromhex(
          "ff093f004b0240061040840410b5b315ec954c3bc79c6a8906aa259afeeb30"
          "14fa8195d2694887e8602c89b322fd6a74e2dc60bdd1cd2e2f1fb67ff622f1"
          "25e8d790fb80217e79c35f98"
      )
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              "id": definitions.CryptoKeyAlgorithm.SHA256,
              "length_bits": 512,
          },
          key_type=definitions.WebCryptoKeyType.SECRET,
          extractable=False,
          usages=definitions.CryptoKeyUsage.VERIFY,
          key_data=(
              b"\x84\x04\x10\xb5\xb3\x15\xec\x95"
              b"\x4c\x3b\xc7\x9c\x6a\x89\x06\xaa"
              b"\x25\x9a\xfe\xeb\x30\x14\xfa\x81"
              b"\x95\xd2\x69\x48\x87\xe8\x60\x2c"
              b"\x89\xb3\x22\xfd\x6a\x74\xe2\xdc"
              b"\x60\xbd\xd1\xcd\x2e\x2f\x1f\xb6"
              b"\x7f\xf6\x22\xf1\x25\xe8\xd7\x90"
              b"\xfb\x80\x21\x7e\x79\xc3\x5f\x98"
          ),
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("RSAHashedKey"):
      serialized_value = bytes.fromhex(
          "ff093f004b040d018008030100010611a2010ac99bea4a34ec34e0795e8d12"
          "254f19938232d88760e71d9ce54249282645729d698623d2a75197b8069cb2"
          "03e3b8dcab5fb4c12bc2d537123d251afb426dd651b364bf50af3125cb981a"
          "b7ac678668f14ccc3428a6c99a3e5c7561a178396e4e1048f85e69f1b43c12"
          "1163687b86d8a8e383f93fa0c6fb0d5a01829b9e7aa457a3842bb6c7ae0ead"
          "eb86c872b32a5ef31a3359e361ba9185f8483b9ab6bfe9e3b3"
      )
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              "id": definitions.CryptoKeyAlgorithm.RSA_PSS,
              "modulus_length_bits": 1024,
              "public_exponent_size": 3,
              "public_exponent_bytes": b"\x01\x00\x01",
              "hash": definitions.CryptoKeyAlgorithm.SHA256,
          },
          key_type=definitions.AsymmetricCryptoKeyType.PUBLIC_KEY,
          extractable=True,
          usages=(
              definitions.CryptoKeyUsage.VERIFY
              | definitions.CryptoKeyUsage.EXTRACTABLE
          ),
          key_data=(
              b"\x0a\xc9\x9b\xea\x4a\x34\xec\x34"
              b"\xe0\x79\x5e\x8d\x12\x25\x4f\x19"
              b"\x93\x82\x32\xd8\x87\x60\xe7\x1d"
              b"\x9c\xe5\x42\x49\x28\x26\x45\x72"
              b"\x9d\x69\x86\x23\xd2\xa7\x51\x97"
              b"\xb8\x06\x9c\xb2\x03\xe3\xb8\xdc"
              b"\xab\x5f\xb4\xc1\x2b\xc2\xd5\x37"
              b"\x12\x3d\x25\x1a\xfb\x42\x6d\xd6"
              b"\x51\xb3\x64\xbf\x50\xaf\x31\x25"
              b"\xcb\x98\x1a\xb7\xac\x67\x86\x68"
              b"\xf1\x4c\xcc\x34\x28\xa6\xc9\x9a"
              b"\x3e\x5c\x75\x61\xa1\x78\x39\x6e"
              b"\x4e\x10\x48\xf8\x5e\x69\xf1\xb4"
              b"\x3c\x12\x11\x63\x68\x7b\x86\xd8"
              b"\xa8\xe3\x83\xf9\x3f\xa0\xc6\xfb"
              b"\x0d\x5a\x01\x82\x9b\x9e\x7a\xa4"
              b"\x57\xa3\x84\x2b\xb6\xc7\xae\x0e"
              b"\xad\xeb\x86\xc8\x72\xb3\x2a\x5e"
              b"\xf3\x1a\x33\x59\xe3\x61\xba\x91"
              b"\x85\xf8\x48\x3b\x9a\xb6\xbf\xe9"
              b"\xe3\xb3"
          ),
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("ECDSA Key"):
      serialized_value = bytes.fromhex(
          "ff093f004b050e0101115bcb981ab7ac678668f14ccc3428a6c99a3e5c7561"
          "a178396e4e1048f85e69f1b43c121163687b86d8a8e383f93fa0c6fb0d5a01"
          "829b9e7aa457a3842bb6c7ae0eadeb86c872b32a5ef31a3359e361ba9185f8"
          "483b9ab6bfe9e3b330"
      )
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              "crypto_key_algorithm": definitions.CryptoKeyAlgorithm.ECDSA,
              "named_curve_type": definitions.NamedCurve.P256,
          },
          key_type=definitions.AsymmetricCryptoKeyType.PUBLIC_KEY,
          extractable=True,
          usages=(
              definitions.CryptoKeyUsage.VERIFY
              | definitions.CryptoKeyUsage.EXTRACTABLE
          ),
          key_data=(
              b"\xcb\x98\x1a\xb7\xac\x67\x86\x68"
              b"\xf1\x4c\xcc\x34\x28\xa6\xc9\x9a"
              b"\x3e\x5c\x75\x61\xa1\x78\x39\x6e"
              b"\x4e\x10\x48\xf8\x5e\x69\xf1\xb4"
              b"\x3c\x12\x11\x63\x68\x7b\x86\xd8"
              b"\xa8\xe3\x83\xf9\x3f\xa0\xc6\xfb"
              b"\x0d\x5a\x01\x82\x9b\x9e\x7a\xa4"
              b"\x57\xa3\x84\x2b\xb6\xc7\xae\x0e"
              b"\xad\xeb\x86\xc8\x72\xb3\x2a\x5e"
              b"\xf3\x1a\x33\x59\xe3\x61\xba\x91"
              b"\x85\xf8\x48\x3b\x9a\xb6\xbf\xe9"
              b"\xe3\xb3\x30"
          ),
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

    with self.subTest("NoParams Key"):
      serialized_value = bytes.fromhex("ff093f004b0611a0020301020300")
      expected_value = blink.CryptoKey(
          algorithm_parameters={
              "crypto_key_algorithm": definitions.CryptoKeyAlgorithm.PBKDF2
          },
          key_type=definitions.WebCryptoKeyType.SECRET,
          extractable=False,
          usages=(
              definitions.CryptoKeyUsage.DRIVE_BITS
              | definitions.CryptoKeyUsage.DERIVE_KEY
          ),
          key_data=b"\x01\x02\x03",
      )
      parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
      self.assertEqual(parsed_value, expected_value)

  def test_ReadDomFileSystem(self) -> None:
    """Tests UnguessableToken decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c64000000")
    expected_value = blink.DOMFileSystem(raw_type=0, name="", root_url="")
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadFileSystemFileHandle(self) -> None:
    """Tests UnguessableToken decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c64000000")
    expected_value = blink.DOMFileSystem(raw_type=0, name="", root_url="")
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadRTCEncodedAudioFrame(self) -> None:
    """Tests Blink RTCEncodedAudioFrame decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c4100")
    expected_value = blink.RTCEncodedAudioFrame(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadRTCEncodedVideoFrame(self) -> None:
    """Tests Blink RTCEncodedVideoFrame decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c5600")
    expected_value = blink.RTCEncodedVideoFrame(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadAudioData(self) -> None:
    """Tests AudioData decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c610000")
    expected_value = blink.AudioData(audio_frame_index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadVideoFrame(self) -> None:
    """Tests VideoFrame decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c7600")
    expected_value = blink.VideoFrame(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadEncodedAudioChunk(self) -> None:
    """Tests UnguessableToken decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c7900")
    expected_value = blink.EncodedAudioChunk(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadEncodedVideoChunk(self) -> None:
    """Tests UnguessableToken decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c7a00")
    expected_value = blink.EncodedVideoChunk(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadMediaStreamTrack(self) -> None:
    """Tests MediaStream decoding."""
    with self.assertRaisesRegex(NotImplementedError, "ReadMediaStream"):
      serialized_value = bytes.fromhex("ff11ff0d5c7300")
      _ = blink.V8ScriptValueDecoder.FromBytes(serialized_value)

  def test_ReadCropTarget(self) -> None:
    """Tests CropTarget decoding."""
    with self.assertRaisesRegex(NotImplementedError, "ReadCropTarget"):
      serialized_value = bytes.fromhex("ff11ff0d5c6300")
      _ = blink.V8ScriptValueDecoder.FromBytes(serialized_value)

  def test_ReadRestrictionTarget(self) -> None:
    """Tests RestrictionTarget decoding."""
    with self.assertRaisesRegex(NotImplementedError, "ReadRestrictionTarget"):
      serialized_value = bytes.fromhex("ff11ff0d5c4400")
      _ = blink.V8ScriptValueDecoder.FromBytes(serialized_value)

  def test_ReadMediaSourceHandle(self) -> None:
    """Tests MediaSourceHandle decoding."""
    serialized_value = bytes.fromhex("ff11ff0d5c5300")
    expected_value = blink.MediaSourceHandle(index=0)
    parsed_value = blink.V8ScriptValueDecoder.FromBytes(serialized_value)
    self.assertEqual(parsed_value, expected_value)

  def test_ReadFencedFrameConfig(self) -> None:
    """Tests FencedFrameConfig decoding."""
    with self.assertRaisesRegex(NotImplementedError, "ReadFencedFrameConfig"):
      serialized_value = bytes.fromhex("ff11ff0d5c4300")
      _ = blink.V8ScriptValueDecoder.FromBytes(serialized_value)


if __name__ == "__main__":
  unittest.main()
