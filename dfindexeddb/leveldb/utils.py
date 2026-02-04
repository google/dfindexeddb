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
"""Helper/utility classes for LevelDB."""
from __future__ import annotations

import io
import struct
from typing import BinaryIO, Tuple, Type, TypeVar

from dfindexeddb import errors, utils


_CHUNK_SIZE = 8
_MARKER = _CHUNK_SIZE + 1
_EMPTY_BINARY_SENTINEL = 0
_SIGN_BIT = 1 << 63
_SENTINEL = 0
_TWO_BYTE_ENCODING_INDICATOR = 0x80
_THREE_BYTE_ENCODING_INDICATOR = 0xFF


class LevelDBDecoder(utils.StreamDecoder):
  """A helper class to decode data types from LevelDB files."""

  def DecodeBool(self) -> Tuple[int, bool]:
    """Returns a Tuple of the offset of decoding and the bool value."""
    offset, buffer = self.ReadBytes(1)
    return offset, buffer[0] is not None

  def DecodeString(self) -> Tuple[int, str]:
    """Returns a tuple of the offset of decoding and the string value.

    Raises:
      errors.DecoderError: when the parsed string buffer is not even (i.e.
          cannot be decoded as a UTF-16-BE string.
    """
    offset = self.stream.tell()
    buffer = self.stream.read()
    if len(buffer) % 2:
      raise errors.DecoderError(
          f"Odd number of bytes encountered at offset {offset}"
      )
    return offset, buffer.decode("utf-16-be")

  def DecodeLengthPrefixedSlice(self) -> Tuple[int, bytes]:
    """Returns a tuple of the offset of decoding and the byte 'slice'."""
    offset, num_bytes = self.DecodeUint32Varint()
    _, blob = self.ReadBytes(num_bytes)
    return offset, blob

  def DecodeBlobWithLength(self) -> Tuple[int, bytes]:
    """Returns a tuple of a the offset of decoding and the binary blob."""
    offset, num_bytes = self.DecodeUint64Varint()
    _, blob = self.ReadBytes(num_bytes)
    return offset, blob

  def DecodeStringWithLength(
      self, encoding: str = "utf-16-be"
  ) -> Tuple[int, str]:
    """Returns a tuple of the offset of decoding and the string value."""
    offset, length = self.DecodeUint64Varint()
    _, buffer = self.ReadBytes(length * 2)
    return offset, buffer.decode(encoding=encoding)

  def DecodeSortableBinary(self) -> Tuple[int, bytes]:
    """Decodes a sortable binary from the binary stream.

    Returns:
      a tuple of the offset and the decoded bytes.

    Raises:
      errors.ParserError: if an invalid tag is encountered.
    """
    output = bytearray()

    offset, first = self.PeekBytes(1)
    if first[0] == _EMPTY_BINARY_SENTINEL:
      self.ReadBytes(1)
      return offset, b""

    while True:
      _, marker_or_sentinel = self.DecodeUint8()
      if marker_or_sentinel == _MARKER:
        _, chunk = self.ReadBytes(_CHUNK_SIZE)
        output.extend(chunk)
        continue
      if 1 <= marker_or_sentinel <= _CHUNK_SIZE:
        payload_len = marker_or_sentinel
        padding_len = _CHUNK_SIZE - payload_len
        if padding_len > 0:
          return offset, bytes(output[:-padding_len])
        return offset, bytes(output)
      raise errors.ParserError(
          f"Invalid marker or sentinel {marker_or_sentinel} in sortable binary"
      )

  def DecodeSortableDouble(self) -> Tuple[int, float]:
    """Decodes a sortable double-precision float from the binary stream.

    Returns:
      a tuple of the offset and the decoded double.
    """
    offset, host_bits = self.DecodeInt(8, byte_order="big", signed=False)
    if host_bits & _SIGN_BIT:
      host_bits ^= _SIGN_BIT
    else:
      host_bits ^= 0xFFFFFFFFFFFFFFFF
    blob = host_bits.to_bytes(8, byteorder="big")
    return offset, struct.unpack(">d", blob)[0]

  def DecodeSortableString(self) -> Tuple[int, str]:
    """Decodes a sortable string from the binary stream.

    Returns:
      a tuple of the offset and the decoded string.

    Raises:
      errors.ParserError: if an invalid byte is encountered.
    """
    output = []
    offset = self.stream.tell()
    while True:
      _, first = self.DecodeUint8()
      if first == _SENTINEL:
        break
      if (first & 0x80) == 0:
        output.append(chr((first & 0x7F) - 1))
      elif (first & 0xC0) == _TWO_BYTE_ENCODING_INDICATOR:
        _, second = self.DecodeUint8()
        output.append(chr(((first & 0x3F) << 8) | second))
      elif first == _THREE_BYTE_ENCODING_INDICATOR:
        _, high = self.DecodeUint8()
        _, low = self.DecodeUint8()
        output.append(chr((high << 8) | low))
      else:
        raise errors.ParserError(f"Invalid byte {first} in sortable string")
    return offset, "".join(output)


T = TypeVar("T")


class FromDecoderMixin:
  """A mixin for parsing dataclass attributes using a LevelDBDecoder."""

  @classmethod
  def FromDecoder(
      cls: Type[T], decoder: LevelDBDecoder, base_offset: int = 0
  ) -> T:
    """Decodes a class type from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      The class instance.

    Raises:
      NotImplementedError if the child class does not implement this method.
    """
    raise NotImplementedError

  @classmethod
  def FromStream(cls: Type[T], stream: BinaryIO, base_offset: int = 0) -> T:
    """Decodes a class type from the current position of a binary stream.

    Args:
      stream: the binary stream.
      base_offset: the base offset of the binary stream.

    Returns:
      The class instance.
    """
    decoder = LevelDBDecoder(stream)
    return cls.FromDecoder(  # type: ignore[attr-defined,no-any-return]
        decoder=decoder, base_offset=base_offset
    )

  @classmethod
  def FromBytes(
      cls: Type[T], raw_data: bytes | bytearray, base_offset: int = 0
  ) -> T:
    """Parses a class type from raw bytes.

    Args:
      raw_data: the raw data.
      base_offset: the base offset of the raw data.

    Returns:
      The class instance.
    """
    stream = io.BytesIO(raw_data)
    return cls.FromStream(  # type: ignore[attr-defined,no-any-return]
        stream=stream, base_offset=base_offset
    )
