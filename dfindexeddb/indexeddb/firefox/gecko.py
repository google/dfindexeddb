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
"""Parsers for Gecko encoded JavaScript values."""
from __future__ import annotations

import dataclasses
import datetime
import io
import os
import struct
from typing import Any, List, Tuple, Union

import snappy

from dfindexeddb import errors
from dfindexeddb import utils
from dfindexeddb.indexeddb import types
from dfindexeddb.indexeddb.firefox import definitions


_FRAME_HEADER = b'\xff\x06\x00\x00sNaPpY'


@dataclasses.dataclass
class IDBKey(utils.FromDecoderMixin):
  """An IndexedDB Key.

  Attributes:
    offset: the offset of the key.
    type: the type of the key.
    value: the value of the key.
  """
  offset: int
  type: definitions.IndexedDBKeyType
  value: Union[bytes, datetime.datetime, float, list, str, None]

  @classmethod
  def FromDecoder(
    cls, decoder: utils.StreamDecoder, base_offset: int = 0) -> IDBKey:
    """Decodes an IndexedDB key from the current position of the decoder.

    Args:
      decoder: the decoder.
      base_offset: the base offset.

    Returns:
      The IndexedDB Key.
    """
    offset, key_type, data = KeyDecoder(decoder.stream).DecodeKey()
    return cls(offset=offset + base_offset, type=key_type, value=data)


class KeyDecoder(utils.StreamDecoder):
  """A helper class to decode the Gecko-encoded key value."""

  def DecodeKey(self) -> Tuple[int, definitions.IndexedDBKeyType, Any]:
    """Decodes the key.

    Returns:
      a tuple comprising the offset where the key was decoded, the key type and
          the key value.
    """
    offset, key_type_bytes = self.PeekBytes(1)
    value = self._DecodeJSValInternal(key_type_bytes[0])
    if key_type_bytes[0] >= definitions.IndexedDBKeyType.ARRAY:
      key_type = definitions.IndexedDBKeyType.ARRAY
    else:
      key_type = definitions.IndexedDBKeyType(key_type_bytes[0])
    return offset, key_type, value

  def _DecodeJSValInternal(
      self,
      key_type: int,
      type_offset: int = 0,
      recursion_depth: int = 0
  ) -> Any:
    """Decodes a Javascript Value.

    Args:
      key_type: the key type byte value.
      type_offset: the type_offset.
      recursion_depth: the current recursion depth.

    Returns:
      the value.

    Raises:
      ParserError: when reaching maximum recursion depth or when an known key
          type has been parsed.
    """
    if recursion_depth == definitions.MAX_RECURSION_DEPTH:
      raise errors.ParserError('Reached Maximum Recursion Depth')

    if key_type - type_offset >= definitions.IndexedDBKeyType.ARRAY:
      type_offset += definitions.IndexedDBKeyType.ARRAY
      if (type_offset ==
          definitions.IndexedDBKeyType.ARRAY * definitions.MAX_ARRAY_COLLAPSE):
        self.stream.seek(1, os.SEEK_CUR)
        type_offset = 0
      value = []
      while (
          self.NumRemainingBytes() and (key_type - type_offset) != (
              definitions.IndexedDBKeyType.TERMINATOR)):
        value.append(
            self._DecodeJSValInternal(
                key_type, type_offset, recursion_depth + 1))
        type_offset = 0
        if self.NumRemainingBytes():
          _, key_bytes = self.PeekBytes(1)
          key_type = key_bytes[0]

      if self.NumRemainingBytes():
        _ = self.ReadBytes(1)  # consume terminator byte

    elif key_type - type_offset == definitions.IndexedDBKeyType.STRING:
      _, value = self._DecodeAsStringy()
      value = value.decode('utf-8')  # TODO: test other text encoding types
    elif key_type - type_offset == definitions.IndexedDBKeyType.DATE:
      _, value = self._DecodeDate()
    elif key_type - type_offset == definitions.IndexedDBKeyType.FLOAT:
      _, value = self._DecodeFloat()
    elif key_type - type_offset == definitions.IndexedDBKeyType.BINARY:
      _, value = self._DecodeAsStringy()
    else:
      raise errors.ParserError(
          f'Unknown key type parsed: {key_type - type_offset}')
    return value

  def _ReadUntilNull(self) -> bytearray:
    """Read bytes until a null (terminator) byte is encountered."""
    result = bytearray()
    num_remaining_bytes = self.NumRemainingBytes()
    while num_remaining_bytes:
      _, c = self.ReadBytes(1)
      if c == b'\x00':
        break
      result += c
      num_remaining_bytes -= 1
    return result

  def _DecodeAsStringy(self, element_size: int = 1) -> Tuple[int, bytes]:
    """Decode a string buffer.

    Args:
      element_size: parse string as a multi-byte string.

    Returns:
      A tuple of the offset and the decoded string.

    Raises:
      ParserError: if an invalid type is read or an unsupported
          encoded byte is encountered
    """
    offset, type_int = self.DecodeUint8()
    if type_int % definitions.IndexedDBKeyType.ARRAY.value not in (
        definitions.IndexedDBKeyType.STRING.value,
        definitions.IndexedDBKeyType.BINARY.value):
      raise errors.ParserError(
          'Invalid type', hex(type_int), hex(type_int % 0x50))

    i = 0
    result = self._ReadUntilNull()
    while i < len(result):
      if not result[i] & 0x80:
        result[i] -= definitions.ONE_BYTE_ADJUST
      elif element_size == 2 or not result[i] & 0x40:
        c = struct.unpack_from('>H', result, i)[0]
        d = c - 0x8000 - definitions.TWO_BYTE_ADJUST
        struct.pack_into('>H', result, i, d)
      else:
        raise errors.ParserError('Unsupported byte')  # TODO: add support here.
      i += 1
    return offset + 1, result

  def _DecodeFloat(self) -> Tuple[int, float]:
    """Decodes a float.

    Returns:
      A tuple of the offset and a (double-precision) float value.

    Raises:
      ParserError if an invalid type is read
    """
    _, type_byte = self.DecodeUint8()
    if type_byte % definitions.IndexedDBKeyType.ARRAY not in (
        definitions.IndexedDBKeyType.FLOAT, definitions.IndexedDBKeyType.DATE):
      raise errors.ParserError(
          'Invalid type', hex(type_byte), hex(type_byte % 0x50))

    float_offset, number_bytes = self.ReadBytes(
        min(8, self.NumRemainingBytes()))

    # pad to 64-bits
    if len(number_bytes) != 8:
      number_bytes += b'\x00'*(8 - len(number_bytes))

    int_value = struct.unpack('>q', number_bytes)[0]

    if int_value & 0x8000000000000000:
      int_value = int_value & 0x7FFFFFFFFFFFFFFF
    else:
      int_value = -int_value
    return float_offset, struct.unpack('>d', struct.pack('>q', int_value))[0]

  def _DecodeBinary(self) -> Tuple[int, bytes]:
    """Decodes a binary value.

    Returns:
      A tuple of the offset and the byte-array.

    Raises:
      ParserError: when an invalid type byte is encountered.
    """
    _, type_byte = self.ReadBytes(1)
    if (type_byte[0] % definitions.IndexedDBKeyType.ARRAY !=
        definitions.IndexedDBKeyType.BINARY):
      raise errors.ParserError(
          f'Invalid type {type_byte[0] % definitions.IndexedDBKeyType.ARRAY}')
    values = bytearray()
    offset = self.stream.tell()
    while self.NumRemainingBytes():
      _, value = self.ReadBytes(1)
      if value == definitions.IndexedDBKeyType.TERMINATOR:
        break
      values.append(value[0])
    return offset, values

  def _DecodeDate(self) -> Tuple[int, datetime.datetime]:
    """Decodes a date.

    Returns:
      A tuple of the offset and the decoded datetime.
    """
    offset, value = self._DecodeFloat()
    return offset, datetime.datetime.fromtimestamp(
        value/1000, tz=datetime.timezone.utc)


class JSStructuredCloneDecoder(utils.FromDecoderMixin):
  """Decodes a serialized JavaScript value.

  Attributes:
    decoder: for decoding the buffer.
    all_objects: all the objects.
  """

  def __init__(self, decoder: utils.StreamDecoder):
    """Initializes the reader.

    Args:
      buffer: the serialized bytes.
    """
    self.decoder = decoder
    self.all_objects: List[Any] = []
    self._object_stack: List[Any] = []

  def _PeekTagAndData(self) -> tuple[int, int]:
    """Peeks Tag and Data values."""
    _, pair_bytes = self.decoder.PeekBytes(8)
    pair = int.from_bytes(pair_bytes, byteorder='little', signed=False)
    tag = pair >> 32
    data = pair & 0x00000000FFFFFFFF
    return tag, data

  def _DecodeTagAndData(self) -> tuple[int, int]:
    """Decodes Tag and Data values."""
    _, pair = self.decoder.DecodeUint64()
    tag = pair >> 32
    data = pair & 0x00000000FFFFFFFF
    return tag, data

  def _DecodeString(self, data: int) -> str:
    """Decodes a String.

    Args:
      data: the data value.

    Returns:
      the decoded string.

    Raises:
      ParserError: if the serialized string length is too large.
    """
    number_chars = data & 0x7FFFFFFF
    latin1 = data & 0x80000000
    if number_chars > definitions.MAX_LENGTH:
      raise errors.ParserError('Bad serialized string length')

    if latin1:
      _, chars = self.decoder.ReadBytes(number_chars)
      chars = chars.decode('latin-1')
    else:
      _, chars = self.decoder.ReadBytes(number_chars*2)
      chars = chars.decode('utf-16-le')

    return chars

  def _DecodeBigInt(self, data: int) -> int:
    """Decodes a BigInteger.

    Args:
      data: the data value

    Returns:
      the decoded integer.
    """
    length = data & 0x7FFFFFFF
    is_negative = data & 0x80000000
    if length == 0:
      return 0
    contents = []
    for _ in range(length):
      _, element = self.decoder.ReadBytes(8)
      contents.extend(element)
    return int.from_bytes(
        contents, byteorder='little', signed=bool(is_negative))

  def _DecodeTypedArray(
      self, array_type: int, number_elements: int, is_version1: bool = False
  ) -> Any:
    """Decodes a typed array.

    Args:
      array_type: the array type.
      number_elements: the number of elements.
      is_version1: True if the typed array is of version 1 type.

    Returns:
      The typed array.
    """
    self.all_objects.append(None)
    dummy_index = len(self.all_objects) - 1

    is_auto_length = number_elements == -1
    if is_auto_length:
      number_elements = 0

    if is_version1:
      value = self._DecodeV1ArrayBuffer(array_type, number_elements)
      _byte_offset = 0
    else:
      value = self._StartRead()
      _byte_offset = self.decoder.DecodeUint64()

    self.all_objects[dummy_index] = value
    return value

  def _DecodeArrayBuffer(
      self, buffer_type: int, data: int
  ) -> bytes:
    """Decodes an ArrayBuffer.

    Args:
      buffer_type: the data type.
      data: the data value.

    Returns:
      the array buffer.
    """
    if buffer_type == definitions.StructuredDataType.ARRAY_BUFFER_OBJECT:
      _, number_bytes = self.decoder.DecodeUint64()
    elif (buffer_type ==
          definitions.StructuredDataType.RESIZABLE_ARRAY_BUFFER_OBJECT):
      _, number_bytes = self.decoder.DecodeUint64()
      _, _max_bytes = self.decoder.DecodeUint64()
    else:
      number_bytes = data

    _, buffer = self.decoder.ReadBytes(number_bytes)
    return buffer

  def _DecodeV1ArrayBuffer(self, array_type: int, number_elements: int):
    """Decodes a V1 ArrayBuffer.

    Not currently implemented.

    Raises:
      NotImplementedError: because it's not yet implemented..
    """
    raise NotImplementedError('V1 Array Buffer not implemented')

  def DecodeValue(self) -> Any:
    """Decodes a Javascript value."""
    if not self._DecodeHeader():
      return None

    tag, _ = self._PeekTagAndData()
    if tag == definitions.StructuredDataType.TRANSFER_MAP_HEADER:
      raise errors.ParserError('Transfer Map is not supported.')

    value = self._StartRead()

    while self._object_stack:
      offset = self.decoder.stream.tell() % 8
      if offset:
        self.decoder.stream.seek(8 - offset, io.SEEK_CUR)
      tag, _ = self._PeekTagAndData()
      obj = self._object_stack[-1]
      if tag == definitions.StructuredDataType.END_OF_KEYS:
        self._object_stack.pop()
        _, _ = self._DecodeTagAndData()
        continue

      expect_key_value_pairs = isinstance(obj, (dict, set))
      key = self._StartRead()
      if isinstance(key, types.Null) and expect_key_value_pairs:
        self._object_stack.pop()
        continue

      if isinstance(obj, types.JSSet):
        obj.values.add(key)
      elif isinstance(obj, types.JSArray):
        field = self._StartRead()
        obj.values[key] = field
      else:
        field = self._StartRead()
        obj[key] = field

    return value

  def _DecodeHeader(self) -> bool:
    """Decodes the header.

    Returns:
      True if the correct header tag is read.

    Raises:
      ParserError: when a header tag is not found.
    """
    tag, _ = self._DecodeTagAndData()
    if tag != definitions.StructuredDataType.HEADER:
      raise errors.ParserError('Header tag not found.')
    return True

  def _DecodeRegexp(self, flags: int):
    """Decodes a regular expression.

    Args:
      flags: the regular expression flags.

    Raises:
      ParserError: when the string tag is not found.
    """
    tag, string_data = self._DecodeTagAndData()
    if tag != definitions.StructuredDataType.STRING:
      raise errors.ParserError('String tag not found')

    pattern = self._DecodeString(string_data)
    return types.RegExp(pattern=pattern, flags=flags)

  def _StartRead(self) -> Any:
    """Reads the start of a serialized value.

    Raises:
      ParserError: when an unsupported StructuredDataType,
          StructuredCloneTag or unknown tag is read.
    """
    tag, data = self._DecodeTagAndData()
    if tag == definitions.StructuredDataType.NULL:
      value = types.Null()
    elif tag == definitions.StructuredDataType.UNDEFINED:
      value = types.Undefined()
    elif tag == definitions.StructuredDataType.INT32:
      value = data
    elif tag == definitions.StructuredDataType.BOOLEAN:
      value = bool(data)
    elif tag == definitions.StructuredDataType.BOOLEAN_OBJECT:
      value = bool(data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.STRING:
      value = self._DecodeString(data)
    elif tag == definitions.StructuredDataType.STRING_OBJECT:
      value = self._DecodeString(data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.NUMBER_OBJECT:
      _, value = self.decoder.DecodeDouble()
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.BIGINT:
      value = self._DecodeBigInt(data)
    elif tag == definitions.StructuredDataType.BIGINT_OBJECT:
      value = self._DecodeBigInt(data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.DATE_OBJECT:
      _, timestamp = self.decoder.DecodeDouble()
      value = datetime.datetime.fromtimestamp(
          timestamp/1000, tz=datetime.timezone.utc)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.REGEXP_OBJECT:
      value = self._DecodeRegexp(data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.ARRAY_OBJECT:
      value = types.JSArray()
      for _ in range(data):
        value.values.append(None)
      self._object_stack.append(value)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.OBJECT_OBJECT:
      value = {}
      self._object_stack.append(value)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.BACK_REFERENCE_OBJECT:
      value = self.all_objects[data]
    elif tag == definitions.StructuredDataType.ARRAY_BUFFER_OBJECT_V2:
      value = self._DecodeArrayBuffer(tag, data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.ARRAY_BUFFER_OBJECT:
      value = self._DecodeArrayBuffer(tag, data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.RESIZABLE_ARRAY_BUFFER_OBJECT:
      value = self._DecodeArrayBuffer(tag, data)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.TYPED_ARRAY_OBJECT_V2:
      _, array_type = self.decoder.DecodeUint64()
      self._DecodeTypedArray(array_type, data)
    elif tag == definitions.StructuredDataType.TYPED_ARRAY_OBJECT:
      _, number_elements = self.decoder.DecodeUint64()
      value = self._DecodeTypedArray(data, number_elements)
    elif tag == definitions.StructuredDataType.MAP_OBJECT:
      value = {}
      self._object_stack.append(value)
      self.all_objects.append(value)
    elif tag == definitions.StructuredDataType.SET_OBJECT:
      value = types.JSSet()
      self._object_stack.append(value)
      self.all_objects.append(value)
    elif tag <= definitions.StructuredDataType.FLOAT_MAX:
      value = struct.unpack('<d', struct.pack('<II', data, tag))[0]
    elif (definitions.StructuredDataType.TYPED_ARRAY_V1_INT8 <= tag
        <= definitions.StructuredDataType.TYPED_ARRAY_V1_UINT8_CLAMPED):
      value = self._DecodeTypedArray(tag, data)
    elif tag in iter(definitions.StructuredDataType):
      raise errors.ParserError(
          'Unsupported StructuredDataType',
          definitions.StructuredDataType(tag))
    elif tag in iter(definitions.StructuredCloneTags):
      raise errors.ParserError(
          'Unsupported StructuredCloneTag',
          definitions.StructuredCloneTags(tag))
    else:
      raise errors.ParserError('Unknown tag', hex(tag))

    # align the stream to an 8 byte boundary
    offset = self.decoder.stream.tell() % 8
    if offset:
      _, _slack_bytes = self.decoder.ReadBytes(8 - offset)

    return value

  @classmethod
  def FromDecoder(
      cls, decoder: utils.StreamDecoder, base_offset: int = 0) -> Any:
    """Decodes the parsed JavaScript object from the StreamDecoder.

    Args:
      decoder: the StreamDecoder.
      base_offset: the base offset.

    Returns:
      The class instance.
    """
    return cls(decoder).DecodeValue()

  @classmethod
  def FromBytes(cls, raw_data: bytes, base_offset: int = 0) -> Any:
    """Returns the parsed JavaScript object from the raw bytes.

    Args:
      raw_data: the raw data to deserialize/parse.

    Returns:
      A python representation of the parsed JavaScript object.
    """
    if raw_data.startswith(_FRAME_HEADER):
      uncompressed_data = bytearray()
      pos = len(_FRAME_HEADER)
      while pos < len(raw_data):
        is_uncompressed = raw_data[pos]
        block_size = int.from_bytes(
            raw_data[pos + 1:pos + 4], byteorder="little", signed=False)
        _masked_checksum = int.from_bytes(
            raw_data[pos + 4: pos + 9], byteorder="little", signed=False)
        if is_uncompressed:
          uncompressed_data += raw_data[pos + 8: pos + 8 + block_size - 4]
        else:
          uncompressed_data += snappy.decompress(
              raw_data[pos + 8: pos + 8 + block_size - 4])
        pos += block_size + 4
    else:
      uncompressed_data = snappy.decompress(raw_data)
    stream = io.BytesIO(uncompressed_data)

    return cls.FromStream(stream=stream, base_offset=base_offset)
