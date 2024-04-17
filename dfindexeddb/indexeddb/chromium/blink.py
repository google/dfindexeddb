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
from typing import Any, Optional, Union

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
class BaseIndex:
  """A base index class."""
  index: int


@dataclass
class BitMap:
  """A Javascript BitMap."""


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
class BlobIndex(BaseIndex):
  """A Javascript BlobIndex class type."""


@dataclass
class CryptoKey:
  """A Javascript CryptoKey class type.

  Attributes:
    algorithm: the CryptoKey algorithm.
    key_type: the CryptoKey type.
    extractable: True if the CryptoKey is extractable.
    usages: the CryptoKey usage.
    key_data: the raw key data.
  """
  algorithm_parameters: dict[str, Any]
  key_type: Union[
      definitions.WebCryptoKeyType, definitions.AsymmetricCryptoKeyType]
  extractable: bool
  usages: definitions.CryptoKeyUsage
  key_data: bytes


@dataclass
class DOMException:
  """A Javascript DOMException.

  Attributes:
    name: the name.
    message: the message.
    stack_unused: the stack unused.
  """
  name: str
  message: str
  stack_unused: str


@dataclass
class DOMFileSystem:
  """A Javascript DOMFileSystem.

  Attributes:
    raw_type: the raw type.
    name: the name.
    root_url: the root URL.
  """
  raw_type: int
  name: str
  root_url: str


@dataclass
class DOMMatrix2D:
  """A Javascript DOMMatrix2D.

  Attributes:
    values: the values.
  """
  values: list[float]


@dataclass
class DOMMatrix2DReadOnly(DOMMatrix2D):
  """A Javascript Read-Only DOMMatrix2D."""


@dataclass
class DOMMatrix:
  """A Javascript DOMMatrix.

  Attributes:
    values: the values.
  """
  values: list[float]


@dataclass
class DOMMatrixReadOnly(DOMMatrix):
  """A Javascript Read-Only DOMMatrix."""


@dataclass
class DOMPoint:
  """A Javascript DOMPoint.

  Attributes:
    x: the X coordinate.
    y: the Y coordinate.
    z: the Z coordinate.
    w: the W coordinate.
  """
  x: float
  y: float
  z: float
  w: float


@dataclass
class DOMPointReadOnly(DOMPoint):
  """A Javascript Read-Only DOMPoint."""


@dataclass
class DOMQuad:
  """A Javascript DOMQuad.

  Attributes:
    p1: the first point.
    p2: the second point.
    p3: the third point.
    p4: the fourth point.
  """
  p1: DOMPoint
  p2: DOMPoint
  p3: DOMPoint
  p4: DOMPoint


@dataclass
class DOMRect:
  """A Javascript DOMRect.

  Attributes:
    x: the X coordinate.
    y: the Y coordinate.
    width: the width.
    height: the height.
  """
  x: float
  y: float
  width: float
  height: float


@dataclass
class DOMRectReadOnly(DOMRect):
  """A Javascript Read-only DOMRect."""


@dataclass
class EncodedAudioChunk(BaseIndex):
  """A Javascript EncodedAudioChunk."""


@dataclass
class EncodedVideoChunk(BaseIndex):
  """A Javascript EncodedVideoChunk."""


@dataclass
class File:
  """A Javascript File.

  Attributes:
    path: the file path.
    name: the file name.
    relative_path: the file relative path.
    uuid: the file UUID.
    type: the file type.
    has_snapshot: True if the file has a snapshot.
    size: the file size.
    last_modified_ms: the file last modified in milliseconds.
    is_user_visible: True if the file is user visible.
  """
  path: str
  name: Optional[str]
  relative_path: Optional[str]
  uuid: str
  type: str
  has_snapshot: int
  size: Optional[int]
  last_modified_ms: Optional[float]
  is_user_visible: int


@dataclass
class FileIndex(BaseIndex):
  """A Javascript FileIndex."""


@dataclass
class FileList:
  """A Javascript FileList.

  Attributes:
    files: the list of files.
  """
  files: list[File]


@dataclass
class FileListIndex:
  """A Javascript FileListIndex.

  Attributes:
    file_indexes: the list of file indexes.
  """
  file_indexes: list[FileIndex]


@dataclass
class FileSystemHandle:
  """A Javascript FileSystemHandle.

  Attributes:
    name: the file system handle name.
    token_index: the file system token index.
  """
  name: str
  token_index: int


@dataclass
class ImageBitmapTransfer(BaseIndex):
  """A Javascript ImageBitmapTransfer."""


@dataclass
class MediaSourceHandle(BaseIndex):
  """A Javascript MediaSourceHandle."""


@dataclass
class MessagePort(BaseIndex):
  """A Javascript MessagePort."""


@dataclass
class MojoHandle(BaseIndex):
  """A Javascript MojoHandle."""


@dataclass
class ReadableStreamTransfer(BaseIndex):
  """A Javascript ReadableStreamTransfer."""


@dataclass
class RTCEncodedAudioFrame(BaseIndex):
  """A Javascript RTCEncodedAudioFrame."""


@dataclass
class RTCEncodedVideoFrame(BaseIndex):
  """A Javascript RTCEncodedVideoFrame."""


@dataclass
class WriteableStreamTransfer(BaseIndex):
  """A Javascript WriteableStreamTransfer."""


@dataclass
class TransformStreamTransfer(BaseIndex):
  """A Javascript TransformStreamTransfer."""


@dataclass
class OffscreenCanvasTransfer:
  """A Javascript Offscreen Canvas Transfer."""
  width: int
  height: int
  canvas_id: int
  client_id: int
  sink_id: int
  filter_quality: int


@dataclass
class UnguessableToken:
  """A Javascript Unguessable Token.

  Attributes:
    high: the high part.
    low: the low part.
  """
  high: int
  low: int


@dataclass
class VideoFrame(BaseIndex):
  """A Javascript VideoFrame."""


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
    _, tag = decoder.DecodeUint8()
    if tag != definitions.BlinkSerializationTag.VERSION:
      return 0

    _, self.version = decoder.DecodeUint32Varint()
    if self.version < self._MIN_VERSION_FOR_SEPARATE_ENVELOPE:
      return 0

    consumed_bytes = decoder.stream.tell()

    if self.version >= self._MIN_WIRE_FORMAT_VERSION:
      _, trailer_offset_tag = decoder.DecodeUint8()
      if (trailer_offset_tag !=
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

  def _ReadAESKey(self) -> tuple[definitions.WebCryptoKeyType, dict[str, Any]]:
    """Reads an AES CryptoKey.

    Returns:
      The AES key algorithm parameters
    """
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm_id = definitions.CryptoKeyAlgorithm(raw_id)

    _, length_bytes = self.deserializer.decoder.DecodeUint32Varint()

    algorithm_parameters = {
        'id': crypto_key_algorithm_id,
        'length_bits': length_bytes*8
    }

    return definitions.WebCryptoKeyType.SECRET, algorithm_parameters

  def _ReadHMACKey(self) -> tuple[definitions.WebCryptoKeyType, dict[str, Any]]:
    """Reads a HMAC CryptoKey.

    Returns:
      The HMAC key algorithm parameters
    """
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
    """Reads an RSA Hashed CryptoKey.

    Returns:
      The RSA Hashed key algorithm parameters
    """
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
    """Reads an EC Key parameters from the current decoder position.

    Returns:
      The EC Key algorithm parameters.
    """
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
    """Reads a ED25519 CryptoKey from the current decoder position.

    Returns:
      The ED25519 key algorithm parameters.
    """
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
    """Reads a No Params CryptoKey from the current decoder position.

    Returns:
      The No Parameters key algorithm parameters.
    """
    _, raw_id = self.deserializer.decoder.DecodeUint32Varint()
    crypto_key_algorithm = definitions.CryptoKeyAlgorithm(raw_id)

    algorithm_parameters = {
        'crypto_key_algorithm': crypto_key_algorithm
    }

    return definitions.WebCryptoKeyType.SECRET, algorithm_parameters

  def _ReadBlob(self) -> Optional[Blob]:
    """Reads a Blob from the current position.

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
    """Reads a BlobIndex from the current decoder position.

    Returns:
      A parsed BlobIndex if the version is greater than 6, None otherwise.
    """
    if self.version < 6:
      return None
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return BlobIndex(index=index)

  def _ReadFile(self) -> Optional[File]:
    """Reads a Javascript File from the current position.

    Returns:
      A File instance, None if the version is less than 3.
    """
    if self.version < 3:
      return None

    path = self.deserializer.ReadUTF8String()
    name = self.deserializer.ReadUTF8String() if self.version >= 4 else None
    relative_path = (
        self.deserializer.ReadUTF8String() if self.version >= 4 else None)
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
    """Reads a FileIndex from the current position.

    Returns:
      A FileIndex, or None if the version is less than 6.
    """
    if self.version < 6:
      return None
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return FileIndex(index=index)

  def _ReadFileList(self) -> Optional[FileList]:
    """Reads a Javascript FileList from the current position.

    Returns:
      A FileList, or None if a File could not be read.
    """
    _, length = self.deserializer.decoder.DecodeUint32Varint()
    files = []
    for _ in range(length):
      decoded_file = self._ReadFile()
      if not decoded_file:
        return None
      files.append(decoded_file)
    return FileList(files=files)

  def _ReadFileListIndex(self) -> Optional[FileListIndex]:
    """Reads a Javascript FileListIndex from the current position.

    Returns:
      A FileListIndex, or None if a FileIndex could not be read.
    """
    _, length = self.deserializer.decoder.DecodeUint32Varint()
    file_indexes = []
    for _ in range(length):
      decoded_file_index = self._ReadFileIndex()
      if not decoded_file_index:
        return None
      file_indexes.append(decoded_file_index)
    return FileListIndex(file_indexes=file_indexes)

  def _ReadImageBitmap(self):
    """Reads an ImageBitmap."""
    raise NotImplementedError('V8ScriptValueDecoder._ReadImageBitmap')

  def _ReadImageBitmapTransfer(self) -> ImageBitmapTransfer:
    """Reads an ImageBitmapTransfer."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return ImageBitmapTransfer(index=index)

  def _ReadImageData(self):
    """Reads an ImageData from the current position."""
    raise NotImplementedError('V8ScriptValueDecoder._ReadImageData')

  def _ReadDOMPoint(self) -> DOMPoint:
    """Reads a DOMPoint from the current position."""
    _, x = self.deserializer.decoder.DecodeDouble()
    _, y = self.deserializer.decoder.DecodeDouble()
    _, z = self.deserializer.decoder.DecodeDouble()
    _, w = self.deserializer.decoder.DecodeDouble()
    return DOMPoint(x=x, y=y, z=z, w=w)

  def _ReadDOMPointReadOnly(self) -> DOMPointReadOnly:
    """Reads a DOMPointReadOnly from the current position."""
    _, x = self.deserializer.decoder.DecodeDouble()
    _, y = self.deserializer.decoder.DecodeDouble()
    _, z = self.deserializer.decoder.DecodeDouble()
    _, w = self.deserializer.decoder.DecodeDouble()
    return DOMPointReadOnly(x=x, y=y, z=z, w=w)

  def _ReadDOMRect(self) -> DOMRect:
    """Reads a DOMRect from the current position."""
    _, x = self.deserializer.decoder.DecodeDouble()
    _, y = self.deserializer.decoder.DecodeDouble()
    _, width = self.deserializer.decoder.DecodeDouble()
    _, height = self.deserializer.decoder.DecodeDouble()
    return DOMRect(x=x, y=y, width=width, height=height)

  def _ReadDOMRectReadOnly(self) -> DOMRectReadOnly:
    """Reads a DOMRectReadOnly from the current position."""
    _, x = self.deserializer.decoder.DecodeDouble()
    _, y = self.deserializer.decoder.DecodeDouble()
    _, width = self.deserializer.decoder.DecodeDouble()
    _, height = self.deserializer.decoder.DecodeDouble()
    return DOMRectReadOnly(x=x, y=y, width=width, height=height)

  def _ReadDOMQuad(self) -> DOMQuad:
    """Reads a DOMQuad from the current position."""
    p1 = self._ReadDOMPoint()
    p2 = self._ReadDOMPoint()
    p3 = self._ReadDOMPoint()
    p4 = self._ReadDOMPoint()
    return DOMQuad(p1=p1, p2=p2, p3=p3, p4=p4)

  def _ReadDOMMatrix2D(self) -> DOMMatrix2D:
    """Reads a Javascript DOMMatrix2D from the current position."""
    values = [self.deserializer.decoder.DecodeDouble()[1] for _ in range(6)]
    return DOMMatrix2D(values=values)

  def _ReadDOMMatrix2DReadOnly(self) -> DOMMatrix2DReadOnly:
    """Reads a Javascript Read-Only DOMMatrix2D from the current position."""
    values = [self.deserializer.decoder.DecodeDouble()[1] for _ in range(6)]
    return DOMMatrix2DReadOnly(values=values)

  def _ReadDOMMatrix(self) -> DOMMatrix:
    """Reads a Javascript DOMMatrix from the current position."""
    values = [self.deserializer.decoder.DecodeDouble()[1] for _ in range(16)]
    return DOMMatrix(values=values)

  def _ReadDOMMatrixReadOnly(self) -> DOMMatrixReadOnly:
    """Reads a Javascript Read-Only DOMMatrix from the current position."""
    values = [self.deserializer.decoder.DecodeDouble()[1] for _ in range(16)]
    return DOMMatrixReadOnly(values=values)

  def _ReadMessagePort(self) -> MessagePort:
    """Reads a MessagePort from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return MessagePort(index=index)

  def _ReadMojoHandle(self) -> MojoHandle:
    """Reads a MojoHandle from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return MojoHandle(index=index)

  def _ReadOffscreenCanvasTransfer(self):
    """Reads a Offscreen Canvas Transfer from the current position."""
    _, width = self.deserializer.decoder.DecodeUint32Varint()
    _, height = self.deserializer.decoder.DecodeUint32Varint()
    _, canvas_id = self.deserializer.decoder.DecodeUint32Varint()
    _, client_id = self.deserializer.decoder.DecodeUint32Varint()
    _, sink_id = self.deserializer.decoder.DecodeUint32Varint()
    _, filter_quality = self.deserializer.decoder.DecodeUint32Varint()

    return OffscreenCanvasTransfer(
        width=width,
        height=height,
        canvas_id=canvas_id,
        client_id=client_id,
        sink_id=sink_id,
        filter_quality=filter_quality)

  def _ReadReadableStreamTransfer(self) -> ReadableStreamTransfer:
    """Reads a Readable Stream Transfer from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return ReadableStreamTransfer(index=index)

  def _ReadWriteableStreamTransfer(self) -> WriteableStreamTransfer:
    """Reads a Writeable Stream Transfer from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return WriteableStreamTransfer(index=index)

  def _ReadTransformStreamTransfer(self) -> TransformStreamTransfer:
    """Reads a TransformStreamTransfer from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return TransformStreamTransfer(index=index)

  def _ReadDOMException(self) -> DOMException:
    """Reads a DOMException from the current position."""
    name = self.deserializer.ReadUTF8String()
    message = self.deserializer.ReadUTF8String()
    stack_unused = self.deserializer.ReadUTF8String()
    return DOMException(name=name, message=message, stack_unused=stack_unused)

  def _ReadRTCEncodedAudioFrame(self) -> RTCEncodedAudioFrame:
    """Reads a RTC Encoded Audio Frame from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return RTCEncodedAudioFrame(index=index)

  def _ReadRTCEncodedVideoFrame(self) -> RTCEncodedVideoFrame:
    """Reads a RTC Encoded Video Frame from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return RTCEncodedVideoFrame(index=index)

  def _ReadCryptoKey(self) -> CryptoKey:
    """Reads a CryptoKey from the current position.

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

  def _ReadAudioData(self) -> AudioData:
    """Reads an AudioData from the current position."""
    _, audio_frame_index = self.deserializer.decoder.DecodeUint32Varint()
    return AudioData(audio_frame_index=audio_frame_index)

  def _ReadDomFileSystem(self) -> DOMFileSystem:
    """Reads an DOMFileSystem from the current position."""
    _, raw_type = self.deserializer.decoder.DecodeUint32Varint()
    name = self.deserializer.ReadUTF8String()
    root_url = self.deserializer.ReadUTF8String()
    return DOMFileSystem(raw_type=raw_type, name=name, root_url=root_url)

  def _ReadFileSystemFileHandle(self) -> FileSystemHandle:
    """Reads a FileSystemHandle from the current position."""
    name = self.deserializer.ReadUTF8String()
    _, token_index = self.deserializer.decoder.DecodeUint32Varint()
    return FileSystemHandle(name=name, token_index=token_index)

  def _ReadVideoFrame(self) -> VideoFrame:
    """Reads the video frame from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return VideoFrame(index=index)

  def _ReadEncodedAudioChunk(self) -> EncodedAudioChunk:
    """Reads the encoded audio chunk from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return EncodedAudioChunk(index=index)

  def _ReadEncodedVideoChunk(self) -> EncodedVideoChunk:
    """Reads the encoded video chunk from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return EncodedVideoChunk(index=index)

  def _ReadMediaStreamTrack(self):
    """Reads the media stream track from the current position."""
    raise NotImplementedError('V8ScriptValueDecoder._ReadMediaStreamTrack')

  def _ReadCropTarget(self):
    """Reads the crop target from the current position."""
    raise NotImplementedError('V8ScriptValueDecoder._ReadCropTarget')

  def _ReadRestrictionTarget(self):
    """Reads the restriction target from the current position."""
    raise NotImplementedError('V8ScriptValueDecoder._ReadRestrictionTarget')

  def _ReadMediaSourceHandle(self) -> MediaSourceHandle:
    """Reads the media source handle from the current position."""
    _, index = self.deserializer.decoder.DecodeUint32Varint()
    return MediaSourceHandle(index=index)

  def _ReadFencedFrameConfig(self):
    """Reads the fenced frame target from the current position."""
    raise NotImplementedError('V8ScriptValueDecoder._ReadFencedFrameConfig')

  def ReadTag(self) -> definitions.BlinkSerializationTag:
    """Reads a blink serialization tag from the current position.

    Returns:
      The blink serialization tag.

    Raises:
      ParserError: if an invalid blink tag is read.
    """
    _, tag_value = self.deserializer.decoder.DecodeUint8()
    try:
      return definitions.BlinkSerializationTag(tag_value)
    except ValueError as err:
      offset = self.deserializer.decoder.stream.tell()
      raise errors.ParserError(
          f'Invalid blink tag encountered at offset {offset}') from err

  def ReadHostObject(self) -> Any:
    """Reads a host object from the current position.

    Returns:
      The Host Object.
    """
    tag = self.ReadTag()
    dom_object = None

    # V8ScriptValueDeserializer
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
    elif tag == definitions.BlinkSerializationTag.FILE_LIST_INDEX:
      dom_object = self._ReadFileListIndex()
    elif tag == definitions.BlinkSerializationTag.IMAGE_BITMAP:
      dom_object = self._ReadImageBitmap()
    elif tag == definitions.BlinkSerializationTag.IMAGE_BITMAP_TRANSFER:
      dom_object = self._ReadImageBitmapTransfer()
    elif tag == definitions.BlinkSerializationTag.IMAGE_DATA:
      dom_object = self._ReadImageData()
    elif tag == definitions.BlinkSerializationTag.DOM_POINT:
      dom_object = self._ReadDOMPoint()
    elif tag ==  definitions.BlinkSerializationTag.DOM_POINT_READ_ONLY:
      dom_object = self._ReadDOMPointReadOnly()
    elif tag == definitions.BlinkSerializationTag.DOM_RECT:
      dom_object = self._ReadDOMRect()
    elif tag == definitions.BlinkSerializationTag.DOM_RECT_READ_ONLY:
      dom_object = self._ReadDOMRectReadOnly()
    elif tag == definitions.BlinkSerializationTag.DOM_QUAD:
      dom_object = self._ReadDOMQuad()
    elif tag == definitions.BlinkSerializationTag.DOM_MATRIX2D:
      dom_object = self._ReadDOMMatrix2D()
    elif tag == definitions.BlinkSerializationTag.DOM_MATRIX2D_READ_ONLY:
      dom_object = self._ReadDOMMatrix2DReadOnly()
    elif tag == definitions.BlinkSerializationTag.DOM_MATRIX:
      dom_object = self._ReadDOMMatrix()
    elif tag == definitions.BlinkSerializationTag.DOM_MATRIX_READ_ONLY:
      dom_object = self._ReadDOMMatrixReadOnly()
    elif tag == definitions.BlinkSerializationTag.MESSAGE_PORT:
      dom_object = self._ReadMessagePort()
    elif tag == definitions.BlinkSerializationTag.MOJO_HANDLE:
      dom_object = self._ReadMojoHandle()
    elif tag == definitions.BlinkSerializationTag.OFFSCREEN_CANVAS_TRANSFER:
      dom_object = self._ReadOffscreenCanvasTransfer()
    elif tag == definitions.BlinkSerializationTag.READABLE_STREAM_TRANSFER:
      dom_object = self._ReadReadableStreamTransfer()
    elif tag == definitions.BlinkSerializationTag.WRITABLE_STREAM_TRANSFER:
      dom_object = self._ReadWriteableStreamTransfer()
    elif tag == definitions.BlinkSerializationTag.TRANSFORM_STREAM_TRANSFER:
      dom_object = self._ReadTransformStreamTransfer()
    elif tag == definitions.BlinkSerializationTag.DOM_EXCEPTION:
      dom_object = self._ReadDOMException()

    # V8ScriptValueDeserializerForModules
    elif tag == definitions.BlinkSerializationTag.CRYPTO_KEY:
      dom_object = self._ReadCryptoKey()
    elif tag == definitions.BlinkSerializationTag.DOM_FILE_SYSTEM:
      dom_object = self._ReadDomFileSystem()
    elif tag == definitions.BlinkSerializationTag.FILE_SYSTEM_FILE_HANDLE:
      dom_object = self._ReadFileSystemFileHandle()
    elif tag == definitions.BlinkSerializationTag.RTC_ENCODED_AUDIO_FRAME:
      dom_object = self._ReadRTCEncodedAudioFrame()
    elif tag == definitions.BlinkSerializationTag.RTC_ENCODED_VIDEO_FRAME:
      dom_object = self._ReadRTCEncodedVideoFrame()
    elif tag == definitions.BlinkSerializationTag.AUDIO_DATA:
      dom_object = self._ReadAudioData()
    elif tag == definitions.BlinkSerializationTag.VIDEO_FRAME:
      dom_object = self._ReadVideoFrame()
    elif tag == definitions.BlinkSerializationTag.ENCODED_AUDIO_CHUNK:
      dom_object = self._ReadEncodedAudioChunk()
    elif tag == definitions.BlinkSerializationTag.ENCODED_VIDEO_CHUNK:
      dom_object = self._ReadEncodedVideoChunk()
    elif tag == definitions.BlinkSerializationTag.MEDIA_STREAM_TRACK:
      dom_object = self._ReadMediaStreamTrack()
    elif tag == definitions.BlinkSerializationTag.CROP_TARGET:
      dom_object = self._ReadCropTarget()
    elif tag == definitions.BlinkSerializationTag.RESTRICTION_TARGET:
      dom_object = self._ReadRestrictionTarget()
    elif tag == definitions.BlinkSerializationTag.MEDIA_SOURCE_HANDLE:
      dom_object = self._ReadMediaSourceHandle()
    elif tag == definitions.BlinkSerializationTag.FENCED_FRAME_CONFIG:
      dom_object = self._ReadFencedFrameConfig()
    return dom_object

  def Deserialize(self) -> Any:
    """Deserializes a Blink SSV.

    The serialization format has two 'envelopes'.
    [version tag] [Blink version] [version tag] [v8 version] ...

    Returns:
      The deserialized script value.

    Raises:
      ParserError: if an unsupported header version was found.
    """
    version_envelope_size = self._ReadVersionEnvelope()
    if self.trailer_size:
      self.deserializer = v8.ValueDeserializer(
          io.BytesIO(
              self.raw_data[version_envelope_size:self.trailer_offset]),
          delegate=self)
    else:
      self.deserializer = v8.ValueDeserializer(
          io.BytesIO(
              self.raw_data[version_envelope_size:]),
          delegate=self)
    is_supported = self.deserializer.ReadHeader()
    if not is_supported:
      raise errors.ParserError('Unsupported header')
    return self.deserializer.ReadValue()

  @classmethod
  def FromBytes(cls, data: bytes) -> Any:
    """Deserializes a Blink SSV from the data array.

    Returns:
      The deserialized script value.
    """
    return cls(data).Deserialize()
