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
"""Utilities for dfindexeddb."""
from __future__ import annotations
import copy
import dataclasses
import io
import os
import struct
from typing import BinaryIO, Tuple, Type, TypeVar


from dfindexeddb import errors


class StreamDecoder:
  """A helper class to decode primitive data types from BinaryIO streams.

   Attributes:
    stream (BinaryIO): the binary stream.
  """

  def __init__(self, stream: BinaryIO):
    """Initializes a StreamDecoder instance.

    Args:
      stream: the binary stream.
    """
    self.stream = stream

  def NumRemainingBytes(self) -> int:
    """Returns the number of bytes available to the decoder.

    Raises:
      errors.DecoderError: if there are a negative number of remaining bytes.
    """
    current_offset = self.stream.tell()
    end_offset = self.stream.seek(0, os.SEEK_END)
    self.stream.seek(current_offset, os.SEEK_SET)
    num_rem_bytes = end_offset - current_offset
    if num_rem_bytes < 0:
      raise errors.DecoderError('Negative number of remaining bytes.')
    return num_rem_bytes

  def ReadBytes(self, count: int = -1) -> Tuple[int, bytes]:
    """Reads a number of bytes or the remaining bytes from the binary stream.

    Args:
      count: the number of bytes to read, if this value is -1 or not provided,
          all the remaining bytes area read.

    Returns:
      the offset where bytes were read from and the bytes that were read.

    Raises:
      errors.DecoderError: if no bytes are available or there are not enough
          bytes to read.
    """
    offset = self.stream.tell()
    buffer = self.stream.read(count)
    if count == -1 and not buffer:
      raise errors.DecoderError(f'No bytes available at offset {offset}')
    if count != -1 and len(buffer) != count:
      raise errors.DecoderError(
          f'Read {len(buffer)} bytes, but wanted {count} at offset {offset}')
    return offset, buffer

  def PeekBytes(self, count: int) -> Tuple[int, bytes]:
    """Peeks a number of bytes from the binary stream.

    Args:
      count: the number of bytes to read, if this value is -1 or not provided,
          all the remaining bytes area read.

    Returns:
      the offset where bytes were read from and the bytes that were read.
    """
    offset, read_bytes = self.ReadBytes(count)
    self.stream.seek(offset, os.SEEK_SET)
    return offset, read_bytes

  def DecodeInt(
      self,
      byte_count: int = -1,
      byte_order: str = 'little',
      signed: bool = True
  ) -> Tuple[int, int]:
    """Decodes an integer from the binary stream.

    Args:
      byte_count: the number of bytes to read.
      byte_order: the endianness of the integer.
      signed: True if twos-complement is used to represent the integer.

    Returns:
      the decoded integer.
    """
    offset, buffer = self.ReadBytes(byte_count)
    return offset, int.from_bytes(buffer, byteorder=byte_order, signed=signed)

  def DecodeUint8(self) -> Tuple[int, int]:
    """Decodes an unsigned 8-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=1, signed=False)

  def DecodeUint16(self) -> Tuple[int, int]:
    """Decodes an unsigned 16-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=2, signed=False)

  def DecodeUint24(self) -> Tuple[int, int]:
    """Decodes an unsigned 24-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=3, signed=False)

  def DecodeUint32(self) -> Tuple[int, int]:
    """Decodes an unsigned 32-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=4, signed=False)

  def DecodeUint48(self) -> Tuple[int, int]:
    """Decodes an unsigned 48-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=6, signed=False)

  def DecodeUint64(self) -> Tuple[int, int]:
    """Decodes an unsigned 64-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=8, signed=False)

  def DecodeInt8(self) -> Tuple[int, int]:
    """Decodes a signed 8-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=1, signed=True)

  def DecodeInt16(self) -> Tuple[int, int]:
    """Decodes a signed 16-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=2, signed=True)

  def DecodeInt24(self) -> Tuple[int, int]:
    """Decodes a signed 24-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=3, signed=True)

  def DecodeInt32(self) -> Tuple[int, int]:
    """Decodes a signed 32-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=4, signed=True)

  def DecodeInt48(self) -> Tuple[int, int]:
    """Decodes a signed 48-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=6, signed=True)

  def DecodeInt64(self) -> Tuple[int, int]:
    """Decodes a signed 64-bit integer from the binary stream."""
    return self.DecodeInt(byte_count=8, signed=True)

  def DecodeDouble(self, little_endian: bool = True) -> Tuple[int, float]:
    """Returns a Tuple of the offset and a double-precision float."""
    offset, blob = self.ReadBytes(8)
    if little_endian:
      value = struct.unpack('<d', blob)[0]
    else:
      value = struct.unpack('>d', blob)[0]
    return offset, value

  def DecodeFloat(self, little_endian: bool = True) -> Tuple[int, float]:
    """Returns a Tuple of the offset and a single-precision float."""
    offset, blob = self.ReadBytes(4)
    if little_endian:
      value = struct.unpack('<f', blob)[0]
    else:
      value = struct.unpack('>f', blob)[0]
    return offset, value

  def DecodeVarint(self, max_bytes: int = 10) -> Tuple[int, int]:
    """Returns a Tuple of the offset and the decoded base128 varint."""
    offset = self.stream.tell()
    varint = 0
    for i in range(0, max_bytes*7, 7):
      _, varint_part = self.ReadBytes(1)
      varint |= (varint_part[0] & 0x7f) << i
      if not varint_part[0] >> 7:
        break
    return offset, varint

  def DecodeZigzagVarint(self, max_bytes: int = 10) -> Tuple[int, int]:
    """Returns a Tuple of the offset and the decoded zigzag varint."""
    (offset, varint) = self.DecodeVarint(max_bytes)
    return offset, (varint >> 1) ^ -(varint & 1)

  def DecodeUint32Varint(self) -> Tuple[int, int]:
    """Decodes a variable unsigned 32-bit integer from the binary stream."""
    return self.DecodeVarint(max_bytes=5)

  def DecodeUint64Varint(self) -> Tuple[int, int]:
    """Decodes a variable unsigned 64-bit integer from the binary stream."""
    return self.DecodeVarint(max_bytes=10)

  def DecodeInt32Varint(self) -> Tuple[int, int]:
    """Decodes a variable signed 32-bit integer from the binary stream."""
    return self.DecodeZigzagVarint(max_bytes=5)

  def DecodeInt64Varint(self) -> Tuple[int, int]:
    """Decodes a variable signed 64-bit integer from the binary stream."""
    return self.DecodeZigzagVarint(max_bytes=10)


T = TypeVar('T')


class FromDecoderMixin:
  """A mixin for parsing dataclass attributes using a LevelDBDecoder."""

  @classmethod
  def FromDecoder(
      cls: Type[T], decoder: StreamDecoder, base_offset: int = 0) -> T:
    """Decodes a class type from the current position of a StreamDecoder.

    Args:
      decoder: the StreamDecoder.
      base_offset: the base offset.

    Returns:
      The class instance.

    Raises:
      NotImplementedError if the child class does not implement this method.
    """
    raise NotImplementedError

  @classmethod
  def FromStream(
      cls: Type[T], stream: BinaryIO, base_offset: int = 0) -> T:
    """Decodes a class type from the current position of a binary stream.

    Args:
      stream: the binary stream.
      base_offset: the base offset of the binary stream.

    Returns:
      The class instance.
    """
    decoder = StreamDecoder(stream)
    return cls.FromDecoder(decoder=decoder, base_offset=base_offset)

  @classmethod
  def FromBytes(
      cls: Type[T], raw_data: bytes, base_offset: int = 0) -> T:
    """Parses a class type from raw bytes.

    Args:
      raw_data: the raw data.
      base_offset: the base offset of the raw data.

    Returns:
      The class instance.
    """
    stream = io.BytesIO(raw_data)
    return cls.FromStream(stream=stream, base_offset=base_offset)


def asdict(obj, *, dict_factory=dict):  # pylint: disable=invalid-name
  """Custom implementation of the asdict dataclasses method to include the
  class name under the __type__ attribute name.
  """
  if not dataclasses.is_dataclass(obj):
    raise TypeError("asdict() should be called on dataclass instances")
  return _asdict_inner(obj, dict_factory)


def _asdict_inner(obj, dict_factory):
  """Custom implementation of the _asdict_inner dataclasses method."""
  if dataclasses.is_dataclass(obj):
    result = [('__type__', obj.__class__.__name__)]
    for f in dataclasses.fields(obj):
      value = _asdict_inner(getattr(obj, f.name), dict_factory)
      result.append((f.name, value))
    return dict_factory(result)

  if isinstance(obj, tuple) and hasattr(obj, '_fields'):
    return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])

  if isinstance(obj, (list, tuple)):
    return type(obj)(_asdict_inner(v, dict_factory) for v in obj)

  if isinstance(obj, dict):
    return type(obj)((_asdict_inner(k, dict_factory),
                      _asdict_inner(v, dict_factory))
                      for k, v in obj.items())

  return copy.deepcopy(obj)
