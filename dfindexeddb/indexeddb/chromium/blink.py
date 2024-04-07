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
"""Parsers for blink javascript serialized objects."""
from __future__ import annotations
from dataclasses import dataclass
import io
from typing import Any, Optional

from dfindexeddb import errors
from dfindexeddb import utils
from dfindexeddb.indexeddb.chromium import definitions
from dfindexeddb.indexeddb.chromium import v8


_MS_PER_SECOND = 1000


@dataclass
class AudioData:
  """A Javascript AudioData class.

  Attributes:
    audio_frame_index: the Audio Frame index.

  """
  audio_frame_index: int


@dataclass
class Blob:
  """A Javascript Blob class type.

  Attributes:
    uuid: the UUID of the Blob.
    type: the type of the Blob.
    size: the size of the Blob.
  """
  uuid: str
  type: str
  size: int


@dataclass
class BlobIndex:
  """A Javascript BlobIndex class type.

  Attributes:
    index: the Blob index.
  """
  index: int


@dataclass
class CryptoKey:
  """A Javascript CryptoKey class type.

  Attributes:
    algorithm: the CryptoKey algorithm

  """
  algorithm_parameters: dict[str, Any]
  key_type: definitions.WebCryptoKeyType | definitions.AsymmetricCryptoKeyType
  extractable: bool
  usages: definitions.CryptoKeyUsage
  #key_data_length: int
  key_data: bytes


@dataclass
class DOMPoint:
  """A Javascript DOMPoint."""
  x: float
  y: float
  z: float
  w: float



@dataclass
class File:
  """A Javascript File."""
  path: str
  name: str
  relative_path: str
  uuid: str
  type: str
  has_snapshot: int
  size: int
  last_modified_ms: int
  is_user_visible: int


@dataclass
class FileIndex:
  """A Javascript FileIndex."""
  index: int


@dataclass
class FileList:
  """A Javascript FileList."""
  files: list[File]


@dataclass
class FileListIndex:
  """A Javascript FileListIndex."""
  file_indexes: list[FileIndex]


@dataclass
class DOMFileSystem:
  """A Javascript DOMFileSystem."""
  raw_type: int
  name: str
  root_url: str


@dataclass
class FileSystemHandle:
  """A Javascript FileSystemHandle."""
  name: str
  token_index: int


@dataclass
class BitMap:
  """A Javascript BitMap."""


@dataclass
class DOMException:
  """A Javascript DOMException."""
  name: str
  message: str
  stack_unused: str


  @classmethod
  def FromDecoder(cls, decoder: v8.ValueDeserializer) -> DOMException:
    """Decodes a DOMException from the current position of the decoder."""
    name = decoder.ReadUTF8String()
    message = decoder.ReadUTF8String()
    stack_unused = decoder.ReadUTF8String()
    return cls(name=name, message=message, stack_unused=stack_unused)


@dataclass
class UnguessableToken:
  """A Javascript Unguessable Token."""


class V8ScriptValueDecoder:
  """A Blink V8 Serialized Script Value (SSV) decoder.

  Attributes:
    deserializer (v8.ValueDeserializer): the V8 value deserializer.
    raw_data (bytes): the raw bytes containing the serialized javascript
        value.
    version (int): the blink version.
  """
  _MIN_VERSION_FOR_SEPARATE_ENVELOPE = 16

  # As defined in trailer_reader.h
  _MIN_WIRE_FORMAT_VERSION = 21

  def __init__(self, raw_data: bytes):
    self.deserializer = None
    self.raw_data = raw_data
    self.version = 0
    self.trailer_offset = None
    self.trailer_size = None

  def _ReadVersionEnvelope(self) -> int:
    """Reads the Blink version envelope.

    Returns:
      The number of bytes consumed reading the Blink version envelope or zero
          if no blink envelope is detected.
    """
    if not self.raw_data:
      return 0

    decoder = utils.StreamDecoder(io.BytesIO(self.raw_data))
    _, tag_value = decoder.DecodeUint8()
    tag = definitions.BlinkSerializationTag(tag_value)
    if tag != definitions.BlinkSerializationTag.VERSION:
      return 0

    _, version = decoder.DecodeUint32Varint()
    if version < self._MIN_VERSION_FOR_SEPARATE_ENVELOPE:
      return 0

    consumed_bytes = decoder.stream.tell()

    if version >= self._MIN_WIRE_FORMAT_VERSION:
      _, trailer_offset_tag = decoder.ReadBytes(1)
      if (trailer_offset_tag[0] !=
          definitions.BlinkSerializationTag.TRAILER_OFFSET):
        raise errors.ParserError('Trailer offset not found')
      _, self.trailer_offset = decoder.DecodeInt(
          byte_count=8, byte_order='big', signed=False)
      _, self.trailer_size = decoder.DecodeInt(
          byte_count=4, byte_order='big', signed=False)
      trailer_offset_data_size = 1 + 8 + 4 # 1 + sizeof(uint64) + sizeof(uint32)
      consumed_bytes += trailer_offset_data_size
      if consumed_bytes >= len(self.raw_data):
        return 0
    return consumed_bytes

  def _ReadUnguessableToken(self):
    _, high = self.deserializer.decoder.DecodeUint64Varint()
    _, low = self.deserializer.decoder.DecodeUint64Varint()
    return {'high': high, 'low': low}

  def _ReadAudioData(self) -> AudioData:
    """Deserializes an AudioData class from the current decoder position.

    Returns:
      An AudioData.
    """
    _, audio_frame_index = self.deserializer.decoder.DecodeUint32Varint()
    return AudioData(audio_frame_index=audio_frame_index)

  def _ReadBlob(self) -> Optional[Blob]:
    """Deserializes a Blob from the current decoder position.

    Returns:
      A Blob if the version is less then 3, None otherwise.
    """
    if self.version and self.version < 3:
      return None

    uuid = self.deserializer.ReadUTF8String()
    blob_type = self.deserializer.ReadUTF8String()
    _, size = self.deserializer.decoder.DecodeUint64Varint()
    return Blob(uuid=uuid, type=blob_type, size=size)

  def _ReadBlobIndex(self) -> Optional[BlobIndex]:
    """Deserializes a BlobIndex from the current decoder position.

    Returns:
      A parsed BlobIndex if the version is greater than 6, None otherwise.
    """
    if self.version and self.version < 6:
      return None
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return BlobIndex(index=index)

  def _ReadAESKey(self) -> tuple[definitions.WebCryptoKeyType, dict[str, Any]]:
    """Deserializes an AES CryptoKey."""
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm_id = definitions.CryptoKeyAlgorithm(raw_id)
    _, length_bytes = self.deserializer.decoder.DecodeUint32Varint()

    algorithm_parameters = {
        'id': crypto_key_algorithm_id,
        'length_bits': length_bytes*8
    }

    return definitions.WebCryptoKeyType.SECRET, algorithm_parameters

  def _ReadHMACKey(self) -> tuple[definitions.WebCryptoKeyType, dict[str, Any]]:
    """Deserializes a HMAC CryptoKey."""
    _, length_bytes = self.deserializer.decoder.DecodeUint32Varint()
    _, raw_hash = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm = definitions.CryptoKeyAlgorithm(raw_hash)

    algorithm_parameters = {
        'id': crypto_key_algorithm,
        'length_bits': length_bytes*8
    }

    return definitions.WebCryptoKeyType.SECRET, algorithm_parameters

  def _ReadRSAHashedKey(
      self
  ) -> tuple[definitions.AsymmetricCryptoKeyType, dict[str, Any]]:
    """Deserializes a RSA Hashed CryptoKey."""
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm = definitions.CryptoKeyAlgorithm(raw_id)

    _, raw_key_type = self.deserializer.decoder.DecodeUint32Varint()
    key_type = definitions.AsymmetricCryptoKeyType(raw_key_type)

    _, modulus_length_bits = self.deserializer.decoder.DecodeUint32Varint()
    _, public_exponent_size = self.deserializer.decoder.DecodeUint32Varint()
    _, public_exponent_bytes = self.deserializer.decoder.ReadBytes(
    count=public_exponent_size)

    _, raw_hash = self.deserializer.decoder.DecodeUint32Varint()
    hash_algorithm = definitions.CryptoKeyAlgorithm(raw_hash)

    algorithm_parameters = {
        'id': crypto_key_algorithm,
        'modulus_length_bits': modulus_length_bits,
        'public_exponent_size': public_exponent_size,
        'public_exponent_bytes': public_exponent_bytes,
        'hash': hash_algorithm
    }

    return key_type, algorithm_parameters

  def _ReadECKey(
      self
  ) -> tuple[definitions.AsymmetricCryptoKeyType, dict[str, Any]]:
    """Deserializes an EC Key parameters from the current decoder position."""
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm = definitions.CryptoKeyAlgorithm(raw_id)

    _, raw_key_type = self.deserializer.decoder.DecodeUint32Varint()
    key_type = definitions.AsymmetricCryptoKeyType(raw_key_type)

    _, raw_named_curve = self.deserializer.decoder.DecodeUint32Varint()
    named_curve_type = definitions.NamedCurve(raw_named_curve)

    algorithm_parameters = {
        'crypto_key_algorithm': crypto_key_algorithm,
        'named_curve_type': named_curve_type
    }

    return key_type, algorithm_parameters

  def _ReadED25519Key(
      self
  ) -> tuple[definitions.AsymmetricCryptoKeyType, dict[str, Any]]:
    """Deserializes a ED25519 CryptoKey from the current decoder position."""
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm = definitions.CryptoKeyAlgorithm(raw_id)

    _, raw_key_type = self.deserializer.decoder.DecodeUint32Varint()
    key_type = definitions.AsymmetricCryptoKeyType(
        raw_key_type)

    algorithm_parameters = {
        'crypto_key_algorithm': crypto_key_algorithm
    }

    return key_type, algorithm_parameters

  def ReadNoParamsKey(
      self
  ) -> tuple[definitions.WebCryptoKeyType, dict[str, Any]]:
    """Deserializes a No Params CryptoKey from the current decoder position."""
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm = definitions.CryptoKeyAlgorithm(raw_id)
    
    algorithm_parameters = {
        'crypto_key_algorithm': crypto_key_algorithm
    }

    return definitions.WebCryptoKeyType.SECRET, algorithm_parameters

  def _ReadCryptoKey(self) -> CryptoKey:
    """Deserializes a CryptoKey from the current decoder position.

    Returns:
      A parsed CryptoKey.
    """
    _, raw_key_byte = self.deserializer.decoder.DecodeUint8()
    key_byte = definitions.CryptoKeySubTag(raw_key_byte)
    if key_byte == definitions.CryptoKeySubTag.AES_KEY:
      key_type, algorithm_parameters = self._ReadAESKey()
    elif key_byte == definitions.CryptoKeySubTag.HMAC_KEY:
      key_type, algorithm_parameters = self._ReadHMACKey()
    elif key_byte == definitions.CryptoKeySubTag.RSA_HASHED_KEY:
      key_type, algorithm_parameters = self._ReadRSAHashedKey()
    elif key_byte == definitions.CryptoKeySubTag.EC_KEY:
      key_type, algorithm_parameters = self._ReadECKey()
    elif key_byte == definitions.CryptoKeySubTag.ED25519_KEY:
      key_type, algorithm_parameters = self._ReadED25519Key()
    elif key_byte == definitions.CryptoKeySubTag.NO_PARAMS_KEY:
      key_type, algorithm_parameters = self.ReadNoParamsKey()

    _, raw_usages = self.deserializer.decoder.DecodeUint32Varint()
    usages = definitions.CryptoKeyUsage(raw_usages)

    extractable = bool(raw_usages & definitions.CryptoKeyUsage.EXTRACTABLE)
    _, key_data_length = self.deserializer.decoder.DecodeUint32Varint()

    _, key_data = self.deserializer.decoder.ReadBytes(count=key_data_length)

    return CryptoKey(
        key_type=key_type,
        algorithm_parameters=algorithm_parameters,
        extractable=extractable,
        usages=usages,
        key_data=key_data
    )

  def _ReadFile(self) -> Optional[File]:
    """Deserializes a Javascript File object.

    Returns:
      A File instance.
    """
    if self.version < 3:
      return None
    path = self.deserializer.ReadUTF8String()
    name = self.deserializer.ReadUTF8String() if self.version >= 4 else None
    relative_path = (self.deserializer.ReadUTF8String()
                     if self.version >= 4 else None)
    uuid = self.deserializer.ReadUTF8String()
    file_type = self.deserializer.ReadUTF8String()
    has_snapshot = (
        self.deserializer.decoder.DecodeUint32Varint()[1]
        if self.version >= 4 else 0)

    if has_snapshot:
      _, size = self.deserializer.decoder.DecodeUint64Varint()
      _, last_modified_ms = self.deserializer.decoder.DecodeDouble()
      if self.version < 8:
        last_modified_ms *= _MS_PER_SECOND
    else:
      size = None
      last_modified_ms = None

    is_user_visible = (
        self.deserializer.decoder.DecodeUint32Varint()[1]
        if self.version >= 7 else 1)

    return File(
        path=path,
        name=name,
        relative_path=relative_path,
        uuid=uuid,
        type=file_type,
        has_snapshot=has_snapshot,
        size=size,
        last_modified_ms=last_modified_ms,
        is_user_visible=is_user_visible)

  def _ReadFileIndex(self) -> Optional[FileIndex]:
    """Deserializes a FileIndex."""
    if self.version < 6:
      return None
    index = self.deserializer.decoder.DecodeUint32Varint()
    return FileIndex(index=index)

  def _ReadFileList(self) -> FileList:
    """Deserializes a Javascript FileList."""
    _, length = self.deserializer.decoder.DecodeUint32Varint()
    files = [self._ReadFile() for _ in range(length)]
    return FileList(files=files)

  def _ReadFileListIndex(self) -> FileListIndex:
    """Deserializes a Javascript FileListIndex."""
    _, length = self.deserializer.decoder.DecodeUint32Varint()
    file_indexes = [self._ReadFileIndex() for _ in range(length)]
    return FileListIndex(file_indexes=file_indexes)

  def _ReadDOMPoint(self) -> DOMPoint:
    """Deserializes a DOMPoint."""
    _, x = self.deserializer.decoder.DecodeDouble()
    _, y = self.deserializer.decoder.DecodeDouble()
    _, z = self.deserializer.decoder.DecodeDouble()
    _, w = self.deserializer.decoder.DecodeDouble()
    return DOMPoint(x=x, y=y, z=z, w=w)

  def _ReadDOMObject(self, tag: definitions.BlinkSerializationTag) -> Any:
    dom_object = None
    if tag == definitions.BlinkSerializationTag.BLOB:
      dom_object = self._ReadBlob()
    elif tag == definitions.BlinkSerializationTag.BLOB_INDEX:
      dom_object = self._ReadBlobIndex()
    elif tag == definitions.BlinkSerializationTag.FILE:
      dom_object = self._ReadFile()
    elif tag == definitions.BlinkSerializationTag.FILE_INDEX:
      dom_object = self._ReadFileIndex()
    elif tag == definitions.BlinkSerializationTag.FILE_LIST:
      dom_object = self._ReadFileList()
    elif tag == definitions.BlinkSerializationTag.IMAGE_BITMAP:
      raise NotImplementedError('BlinkSerializationTag.IMAGE_BITMAP')
    elif tag == definitions.BlinkSerializationTag.IMAGE_BITMAP_TRANSFER:
      raise NotImplementedError('BlinkSerializationTag.IMAGE_BITMAP_TRANSFER')
    elif tag == definitions.BlinkSerializationTag.IMAGE_DATA:
      raise NotImplementedError('BlinkSerializationTag.IMAGE_DATA')
    elif tag in (
        definitions.BlinkSerializationTag.DOM_POINT,
        definitions.BlinkSerializationTag.DOM_POINT_READ_ONLY):
      dom_object = self._ReadDOMPoint()
    elif tag == definitions.BlinkSerializationTag.DOM_RECT:
      raise NotImplementedError('BlinkSerializationTag.DOM_RECT')
    elif tag == definitions.BlinkSerializationTag.DOM_QUAD:
      raise NotImplementedError('BlinkSerializationTag.DOM_QUAD')
    elif tag == definitions.BlinkSerializationTag.DOM_RECT_READ_ONLY:
      raise NotImplementedError('BlinkSerializationTag.DOM_RECT_READ_ONLY')
    elif tag in (
        definitions.BlinkSerializationTag.DOM_MATRIX2D,
        definitions.BlinkSerializationTag.DOM_MATRIX2D_READ_ONLY):
      raise NotImplementedError('BlinkSerializationTag.DOM_MATRIX2D')
    elif tag in (
        definitions.BlinkSerializationTag.DOM_MATRIX,
        definitions.BlinkSerializationTag.DOM_MATRIX_READ_ONLY):
      raise NotImplementedError('BlinkSerializationTag.DOM_MATRIX')
    elif tag == definitions.BlinkSerializationTag.MESSAGE_PORT:
      raise NotImplementedError('BlinkSerializationTag.MESSAGE_PORT')
    elif tag == definitions.BlinkSerializationTag.MOJO_HANDLE:
      raise NotImplementedError('BlinkSerializationTag.MOJO_HANDLE')
    elif tag == definitions.BlinkSerializationTag.OFFSCREEN_CANVAS_TRANSFER:
      raise NotImplementedError(
          'BlinkSerializationTag.OFFSCREEN_CANVAS_TRANSFER')
    elif tag == definitions.BlinkSerializationTag.READABLE_STREAM_TRANSFER:
      raise NotImplementedError(
          'BlinkSerializationTag.READABLE_STREAM_TRANSFER')
    elif tag == definitions.BlinkSerializationTag.WRITABLE_STREAM_TRANSFER:
      raise NotImplementedError(
          'BlinkSerializationTag.IMAGWRITABLE_STREAM_TRANSFERE_DATA')
    elif tag == definitions.BlinkSerializationTag.DOM_EXCEPTION:
      raise NotImplementedError('BlinkSerializationTag.DOM_EXCEPTION')

    # V8ScriptValueDeserializerForModules
    elif tag == definitions.BlinkSerializationTag.CRYPTO_KEY:
      dom_object = self._ReadCryptoKey()
    elif tag == definitions.BlinkSerializationTag.DOM_FILE_SYSTEM:
      dom_object = self._ReadDomFileSystem()
    elif tag == definitions.BlinkSerializationTag.FILE_SYSTEM_FILE_HANDLE:
      dom_object = self._ReadFileSystemFileHandle()
    elif tag == definitions.BlinkSerializationTag.RTC_ENCODED_AUDIO_FRAME:
      raise NotImplementedError('BlinkSerializationTag.RTC_ENCODED_AUDIO_FRAME')
    elif tag == definitions.BlinkSerializationTag.RTC_ENCODED_VIDEO_FRAME:
      raise NotImplementedError('BlinkSerializationTag.RTC_ENCODED_VIDEO_FRAME')
    elif tag == definitions.BlinkSerializationTag.AUDIO_DATA:
      raise NotImplementedError('BlinkSerializationTag.AUDIO_DATA')
    elif tag == definitions.BlinkSerializationTag.VIDEO_FRAME:
      raise NotImplementedError('BlinkSerializationTag.VIDEO_FRAME')
    elif tag == definitions.BlinkSerializationTag.ENCODED_AUDIO_CHUNK:
      raise NotImplementedError('BlinkSerializationTag.ENCODED_AUDIO_CHUNK')
    elif tag == definitions.BlinkSerializationTag.ENCODED_VIDEO_CHUNK:
      raise NotImplementedError('BlinkSerializationTag.ENCODED_VIDEO_CHUNK')
    elif tag == definitions.BlinkSerializationTag.MEDIA_STREAM_TRACK:
      raise NotImplementedError('BlinkSerializationTag.MEDIA_STREAM_TRACK')
    elif tag == definitions.BlinkSerializationTag.CROP_TARGET:
      raise NotImplementedError('BlinkSerializationTag.CROP_TARGET')
    elif tag == definitions.BlinkSerializationTag.MEDIA_SOURCE_HANDLE:
      raise NotImplementedError('BlinkSerializationTag.MEDIA_SOURCE_HANDLE')
    return dom_object

  def _ReadDomFileSystem(self):
    raw_type = self.deserializer.decoder.DecodeUint32Varint()[1]
    # if raw_type > kMAXVALUE:
    # return None
    name = self.deserializer.ReadUTF8String()
    root_url = self.deserializer.ReadUTF8String()
    return DOMFileSystem(raw_type=raw_type, name=name, root_url=root_url)

  def _ReadFileSystemFileHandle(self):
    name = self.deserializer.ReadUTF8String()
    token_index = self.deserializer.decoder.DecodeUint32Varint()[1]
    return FileSystemHandle(name=name, token_index=token_index)

  def _ReadOffscreenCanvasTransfer(self):
    """Reads the offscreen canvas transfer."""
    raise NotImplementedError('')

  def _ReadRTCEncodedAudioFrame(self):
    """Reads the RTC encoded audio frame."""
    raise NotImplementedError('')

  def _ReadRTCEncodedVideoFrame(self):
    """Reads the RTC encoded video frame."""
    raise NotImplementedError('')

  def _ReadAudioData(self):
    """Reads the audio data."""
    raise NotImplementedError('')

  def _ReadVideoFrame(self):
    """Reads the video frame."""
    raise NotImplementedError('')

  def _ReadEncodedAudioChunk(self):
    """Reads the encoded audio chunk."""
    raise NotImplementedError('')

  def _ReadEncodedVideoChunk(self):
    """Reads the encoded video chunk."""
    raise NotImplementedError('')

  def _ReadMediaStreamTrack(self):
    """Reads the media stream track."""
    raise NotImplementedError('')

  def _ReadCropTarget(self):
    """Reads the crop target."""
    raise NotImplementedError('')

  def _ReadMediaSourceHandle(self):
    """Reads the media source handle."""
    raise NotImplementedError('')

  def GetWasmModuleFromId(self, wasm_module_id: int):
    """Gets the Wasm module from an identifier."""
    raise NotImplementedError('V8ScriptValueDecoder.GetWasmModuleFromId')

  def GetSharedArrayBufferFromId(self, buffer_id: int):
    """Gets the shared array buffer from an identifier."""
    raise NotImplementedError('V8ScriptValueDecoder.GetSharedArrayBufferFromId')

  def ReadTag(self) -> definitions.BlinkSerializationTag:
    """Reads a blink serialization tag.

    Returns:
      The blink serialization tag.
    """
    _, tag_value = self.deserializer.decoder.DecodeUint8()
    return definitions.BlinkSerializationTag(tag_value)

  def ReadHostObject(self) -> Any:
    """Reads a host DOM object.

    Raises:
      NotImplementedError: when called.
    """
    tag = self.ReadTag()
    return self._ReadDOMObject(tag)

  def Deserialize(self) -> Any:
    """Deserializes a Blink SSV.

    The serialization format has two 'envelopes'.
    [version tag] [Blink version] [version tag] [v8 version] ...

    Returns:
      The deserialized script value.
    """
    version_envelope_size = self._ReadVersionEnvelope()
    if self.trailer_size:
      self.deserializer = v8.ValueDeserializer(
          io.BytesIO(self.raw_data[
              version_envelope_size:self.trailer_offset]),
          delegate=self)
    else:
      self.deserializer = v8.ValueDeserializer(
          io.BytesIO(self.raw_data[version_envelope_size:]), delegate=self)
    v8_version = self.deserializer.ReadHeader()
    if not self.version:
      self.version = v8_version
    return self.deserializer.ReadValue()

  @classmethod
  def FromBytes(cls, data: bytes) -> Any:
    """Deserializes a Blink SSV from the data array.

    Returns:
      The deserialized script value.
    """
    return cls(data).Deserialize()
