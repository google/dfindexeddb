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
"""Parsers for v8 javascript serialized objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import io
import os
from typing import Any, BinaryIO, Dict, Optional, Set, Tuple, Union

from dfindexeddb import errors
from dfindexeddb import utils
from dfindexeddb.indexeddb.chromium import definitions


@dataclass
class ArrayBufferView:
  """A parsed Javascript ArrayBufferView."""
  buffer: bytes
  tag: definitions.V8ArrayBufferViewTag
  offset: int
  length: int
  flags: int


@dataclass
class JSArray:
  """A parsed Javascript array.

  A Javascript array behaves like a Python list but allows assigning arbitrary
  properties.  The array is stored in the attribute __array__.
  """
  def __init__(self):
    self.__array__ = []

  def Append(self, element: Any):
    """Appends a new element to the array."""
    self.__array__.append(element)

  def __repr__(self):
    array_entries = ', '.join(
        [str(entry) for entry in list(self.__array__)])
    properties = ', '.join(
        f'{key}: {value}' for key, value in self.properties.items())
    return f'[{array_entries}, {properties}]'

  @property
  def properties(self) -> Dict[str, Any]:
    """Returns the object properties."""
    return self.__dict__

  def __eq__(self, other: JSArray):
    return (
        self.__array__ == other.__array__
        and self.properties == other.properties)

  def __contains__(self, item):
    return item in self.__dict__

  def __getitem__(self, name):
    return self.__dict__[name]


@dataclass
class Null:
  """A parsed Javascript Null."""


@dataclass
class RegExp:
  """A parsed Javascript RegExp."""
  pattern: str
  flags: int


@dataclass(frozen=True)
class Undefined:
  """A parsed Javascript undef."""


class ValueDeserializer:
  """A class to deserialize v8 Javascript values/objects.

  Attributes:
    decoder (utils.StreamDecoder): A StreamDecoder that wraps the binary
      stream containing the serialized Javascript value/object.
    delegate: An instance to delegate deserializing an object
    next_id (int): the next ID to use for a deserialized object.
    objects (dict[int, Any]): a dictionary mapping integer IDs to a
      deserialized object.
    version (int): the version of the serialized Javascript value/object
  """

  LATEST_VERSION = 15

  def __init__(self, stream: BinaryIO, delegate):
    """Initializes a ValueDeserializer.

    Args:
      stream: a stream of bytes to be deserialized.
      delegate: an object to delegate additional deserialization of additional
        Javascript types/objects.
    """
    self.decoder = utils.StreamDecoder(stream)
    self.delegate = delegate
    self.next_id = 0
    self.objects = {}
    self.version = None

  def GetWireFormatVersion(self) -> int:
    """Returns the underlying wire format version.

    Note: Return value is only valid after a call to ReadHeader.
    """
    return self.version

  def ReadHeader(self) -> bool:
    """Reads the header and returns True if the version is supported."""
    if self._ReadTag() != definitions.V8SerializationTag.VERSION:
      return False
    _, self.version = self.decoder.DecodeUint32Varint()
    if self.version > self.LATEST_VERSION:
      return False
    return True

  def ReadObjectWrapper(self):
    """Deserializes a V8 object from the current decoder position."""
    original_position = self.decoder.stream.tell()
    result = self._ReadObject()
    if result is None and self.version == 13:
      self.decoder.stream.seek(original_position, os.SEEK_SET)
      result = self._ReadObject()
      raise NotImplementedError('ValueDeserializer.ReadObjectWrapper v13')
    return result

  def ReadObjectUsingEntireBufferForLegacyFormat(self):
    """Reads an object, consuming the entire buffer."""
    raise NotImplementedError(
        'ValueDeserializer.ReadObjectUsingEntireBufferForLegacyFormat')

  def ReadValue(self):
    """Reads the Javascript value."""
    if self.GetWireFormatVersion() > 0:
      return self.ReadObjectWrapper()
    return self.ReadObjectUsingEntireBufferForLegacyFormat()

  def _PeekTag(self) -> Optional[definitions.V8SerializationTag]:
    """Peeks the next serialization tag from the current decoder position.

    Returns:
      The serialization tag or None if there is no more bytes to read.
    """
    try:
      _, tag_value = self.decoder.PeekBytes(1)
    except errors.DecoderError:
      return None
    try:
      return definitions.V8SerializationTag(tag_value[0])
    except ValueError as error:
      raise errors.ParserError(
          f'Invalid v8 tag value {tag_value} at offset'
          f' {self.decoder.stream.tell()}') from error

  def _ReadTag(self) -> definitions.V8SerializationTag:
    """Returns the next non-padding serialization tag.

    Raises:
      errors.ParserError: when an invalid v8 tag is read.
    """
    while True:
      _, tag_value = self.decoder.ReadBytes(1)
      try:
        tag = definitions.V8SerializationTag(tag_value[0])
      except ValueError as error:
        raise errors.ParserError(f'Invalid v8 tag value {tag_value}') from error
      if tag != definitions.V8SerializationTag.PADDING:
        return tag

  def _ConsumeTag(self, peeked_tag: definitions.V8SerializationTag):
    """Consumes the next serialization tag.

    Args:
      peeked_tag: the tag that is expected to be read from the current position.

    Raises:
      errors.ParserError: if the peeked tag is not read.
    """
    tag = self._ReadTag()
    if tag != peeked_tag:
      raise errors.ParserError(f'Unexpected tag {tag} found.')

  def _ReadObject(self):
    """Reads a Javascript object from the current position."""
    _, result = self._ReadObjectInternal()
    tag = self._PeekTag()
    if tag and tag == definitions.V8SerializationTag.ARRAY_BUFFER_VIEW:
      self._ConsumeTag(tag)
      result = self._ReadJSArrayBufferView(result)
      self.objects[self._GetNextId()] = result
    return result

  def _ReadObjectInternal(self) -> Tuple[definitions.V8SerializationTag, Any]:
    """Reads a Javascript object from the current position.

    Returns:
      a tuple of the serialization tag and the parsed object.
    """
    tag = self._ReadTag()
    if tag == definitions.V8SerializationTag.VERIFY_OBJECT_COUNT:
      _ = self.decoder.DecodeUint32Varint()
      parsed_object = self._ReadObject()
    elif tag == definitions.V8SerializationTag.UNDEFINED:
      parsed_object = Undefined()
    elif tag == definitions.V8SerializationTag.NULL:
      parsed_object = Null()
    elif tag == definitions.V8SerializationTag.TRUE:
      parsed_object = True
    elif tag == definitions.V8SerializationTag.FALSE:
      parsed_object = False
    elif tag == definitions.V8SerializationTag.INT32:
      _, parsed_object = self.decoder.DecodeInt32Varint()
    elif tag == definitions.V8SerializationTag.UINT32:
      _, parsed_object = self.decoder.DecodeUint32Varint()
    elif tag == definitions.V8SerializationTag.DOUBLE:
      _, parsed_object = self.decoder.DecodeDouble()
    elif tag == definitions.V8SerializationTag.BIGINT:
      parsed_object = self.ReadBigInt()
    elif tag == definitions.V8SerializationTag.UTF8_STRING:
      parsed_object = self.ReadUTF8String()
    elif tag == definitions.V8SerializationTag.ONE_BYTE_STRING:
      parsed_object = self.ReadOneByteString()
    elif tag == definitions.V8SerializationTag.TWO_BYTE_STRING:
      parsed_object = self.ReadTwoByteString()
    elif tag == definitions.V8SerializationTag.OBJECT_REFERENCE:
      _, object_id = self.decoder.DecodeUint32Varint()
      parsed_object = self.objects[object_id]
    elif tag == definitions.V8SerializationTag.BEGIN_JS_OBJECT:
      parsed_object = self._ReadJSObject()
    elif tag == definitions.V8SerializationTag.BEGIN_SPARSE_JS_ARRAY:
      parsed_object = self.ReadSparseJSArray()
    elif tag == definitions.V8SerializationTag.BEGIN_DENSE_JS_ARRAY:
      parsed_object = self.ReadDenseJSArray()
    elif tag == definitions.V8SerializationTag.DATE:
      parsed_object = self._ReadJSDate()
    elif tag in (
        definitions.V8SerializationTag.TRUE_OBJECT,
        definitions.V8SerializationTag.FALSE_OBJECT,
        definitions.V8SerializationTag.NUMBER_OBJECT,
        definitions.V8SerializationTag.BIGINT_OBJECT,
        definitions.V8SerializationTag.STRING_OBJECT):
      parsed_object = self._ReadJSPrimitiveWrapper(tag)
    elif tag == definitions.V8SerializationTag.REGEXP:
      parsed_object = self._ReadJSRegExp()
    elif tag == definitions.V8SerializationTag.BEGIN_JS_MAP:
      parsed_object = self._ReadJSMap()
    elif tag == definitions.V8SerializationTag.BEGIN_JS_SET:
      parsed_object = self._ReadJSSet()
    elif tag == definitions.V8SerializationTag.ARRAY_BUFFER:
      parsed_object = self._ReadJSArrayBuffer(
          is_shared=False, is_resizable=False)
    elif tag == definitions.V8SerializationTag.RESIZABLE_ARRAY_BUFFER:
      parsed_object = self._ReadJSArrayBuffer(
          is_shared=False, is_resizable=True)
    elif tag == definitions.V8SerializationTag.SHARED_ARRAY_BUFFER:
      parsed_object = self._ReadJSArrayBuffer(
          is_shared=True, is_resizable=False)
    elif tag == definitions.V8SerializationTag.ERROR:
      parsed_object = self._ReadJSError()
    elif tag == definitions.V8SerializationTag.WASM_MODULE_TRANSFER:
      parsed_object = self._ReadWasmModuleTransfer()
    elif tag == definitions.V8SerializationTag.WASM_MEMORY_TRANSFER:
      parsed_object = self._ReadWasmMemory()
    elif tag == definitions.V8SerializationTag.HOST_OBJECT:
      parsed_object = self.ReadHostObject()
    elif (
        tag == definitions.V8SerializationTag.SHARED_OBJECT and
            self.version >= 15):
      parsed_object = self.ReadSharedObject()
    elif self.version < 13:
      self.decoder.stream.seek(-1, os.SEEK_CUR)
      parsed_object = self.ReadHostObject()
    else:
      parsed_object = None
    return tag, parsed_object

  def ReadString(self) -> str:
    """Reads a string from the current position.

    Raises:
      errors.ParserError: if the parsed object is not a string.
    """
    if self.version < 12:
      return self.ReadUTF8String()

    str_obj = self._ReadObject()
    if not isinstance(str_obj, str):
      raise errors.ParserError('Not a string')
    return str_obj

  def ReadBigInt(self) -> int:
    """Reads a Javascript Bigint from the current position."""
    bit_field = self.decoder.DecodeUint32Varint()[1]
    byte_count = bit_field >> 1
    signed = bool(bit_field & 0x1)
    _, bigint = self.decoder.DecodeInt(byte_count=byte_count)
    return -bigint if signed else bigint

  def ReadUTF8String(self) -> str:
    """Reads a UTF-8 string from the current position."""
    count = self.decoder.DecodeUint32Varint()[1]
    buffer = self.decoder.ReadBytes(count=count)[1]
    return buffer.decode('utf-8')

  def ReadOneByteString(self) -> str:
    """Reads a one-byte string from the current position.

    The raw bytes are decoded using latin-1 encoding.
    """
    length = self.decoder.DecodeUint32Varint()[1]
    buffer = self.decoder.ReadBytes(count=length)[1]
    return buffer.decode('latin-1')

  def ReadTwoByteString(self) -> str:
    """Reads a UTF-16-LE string from the current position."""
    length = self.decoder.DecodeUint32Varint()[1]
    buffer = self.decoder.ReadBytes(count=length)[1]
    return buffer.decode('utf-16-le')

  def ReadExpectedString(self) -> Optional[str]:
    """Reads a string from the current position, None if there is no tag or
      invalid byte length.

    A string can be UTF-8/one-byte/two-byte.

    Raises:
      errors.ParserError: if there is an unexpected serialization tag."""
    tag = self._ReadTag()
    if not tag:
      return None
    _, byte_length = self.decoder.DecodeUint32Varint()
    if not byte_length:
      return None

    _, raw_bytes = self.decoder.ReadBytes(count=byte_length)

    if tag == definitions.V8SerializationTag.ONE_BYTE_STRING:
      return raw_bytes.decode('latin-1')
    if tag == definitions.V8SerializationTag.TWO_BYTE_STRING:
      return raw_bytes.decode('utf-16-le')
    if tag == definitions.V8SerializationTag.UTF8_STRING:
      return raw_bytes.decode('utf-8')
    raise errors.ParserError(f'Unexpected serialization tag {tag}.')

  def _ReadJSObject(self) -> Dict:
    """Reads a JSObject from the current position.

    Raises:
      errors.ParserError: if an unexpected number of properties have been
        read.
    """
    next_id = self._GetNextId()
    js_object = {}

    num_properties = self._ReadJSObjectProperties(
        js_object, definitions.V8SerializationTag.END_JS_OBJECT)
    _, expected_number_properties = self.decoder.DecodeUint32Varint()
    if expected_number_properties != num_properties:
      raise errors.ParserError('Unexpected number of properties')

    self.objects[next_id] = js_object
    return js_object

  def _ReadJSObjectProperties(
      self,
      js_object: Union[Dict, JSArray],
      end_tag: definitions.V8SerializationTag
  ) -> int:
    """Reads key-value properties and sets them to the given js_object.

    Args:
      js_object: the Javascript object to set the parsed properties to.
      end_tag: the end tag that signifies there are no more properties to read.

    Returns:
      the number of properties that were read.
    """
    num_properties = 0
    while self._PeekTag() != end_tag:
      key = self._ReadObject()
      value = self._ReadObject()
      if isinstance(js_object, dict):
        js_object[key] = value
      else:
        js_object.properties[key] = value
      num_properties += 1
    self._ConsumeTag(end_tag)
    return num_properties

  def _GetNextId(self) -> int:
    """Gets the next object ID."""
    next_id = self.next_id
    self.next_id += 1
    return next_id

  def ReadSparseJSArray(self) -> JSArray:
    """Reads a sparse encoded JSArray from the current position.

    Raises:
      errors.ParserError: if there is an unexpected property or array length.
    """
    next_id = self._GetNextId()

    js_array = JSArray()
    _, length = self.decoder.DecodeUint32Varint()
    for _ in range(length):
      js_array.Append(Undefined())

    num_properties = self._ReadJSObjectProperties(
        js_array.__dict__, definitions.V8SerializationTag.END_SPARSE_JS_ARRAY)
    _, expected_num_properties = self.decoder.DecodeUint32Varint()
    _, expected_length = self.decoder.DecodeUint32Varint()

    if num_properties != expected_num_properties:
      raise errors.ParserError('Unexpected property length')
    if length != expected_length:
      raise errors.ParserError('Unexpected array length')
    self.objects[next_id] = js_array
    return js_array

  def ReadDenseJSArray(self) -> JSArray:
    """Reads a dense encoded JSArray from the current position.

    Raises:
      errors.ParserError: if there is an unexpected property or array length.
    """
    next_id = self._GetNextId()

    js_array = JSArray()
    _, length = self.decoder.DecodeUint32Varint()
    for _ in range(length):
      tag = self._PeekTag()
      if tag == definitions.V8SerializationTag.THE_HOLE:
        self._ConsumeTag(tag)
        continue
      array_object = self._ReadObject()

      if self.version < 11 and isinstance(array_object, Undefined):
        continue
      js_array.Append(array_object)

    num_properties = self._ReadJSObjectProperties(
        js_array.__dict__, definitions.V8SerializationTag.END_DENSE_JS_ARRAY)
    _, expected_num_properties = self.decoder.DecodeUint32Varint()
    _, expected_length = self.decoder.DecodeUint32Varint()
    if num_properties != expected_num_properties:
      raise errors.ParserError('Unexpected property length')
    if length != expected_length:
      raise errors.ParserError('Unexpected array length')
    self.objects[next_id] = js_array
    return js_array

  def _ReadJSDate(self) -> datetime:
    """Reads a JSDate from the current position."""
    next_id = self._GetNextId()

    _, value = self.decoder.DecodeDouble()
    result = datetime.utcfromtimestamp(value/1000.0)
    self.objects[next_id] = result
    return result

  def _ReadJSPrimitiveWrapper(
      self,
      tag: definitions.V8SerializationTag
  ) -> Union[bool, float, int, str]:
    """Reads a Javascript wrapped primitive.

    Args:
      tag: the serialization tag.

    Returns:
      the parsed value.

    Raises:
      errors.ParserError: if the given tag is not a Javascript wrapped
        primitive.
    """
    next_id = self._GetNextId()

    if tag == definitions.V8SerializationTag.TRUE_OBJECT:
      value = True
    elif tag == definitions.V8SerializationTag.FALSE_OBJECT:
      value = False
    elif tag == definitions.V8SerializationTag.NUMBER_OBJECT:
      _, value = self.decoder.DecodeDouble()
    elif tag == definitions.V8SerializationTag.BIGINT_OBJECT:
      value = self.ReadBigInt()
    elif tag == definitions.V8SerializationTag.STRING_OBJECT:
      value = self.ReadString()
    else:
      raise errors.ParserError(f'Invalid tag {tag}')

    self.objects[next_id] = value
    return value

  def _ReadJSRegExp(self) -> RegExp:
    """Reads a Javascript regular expression from the current position."""
    next_id = self._GetNextId()
    pattern = self.ReadString()
    _, flags = self.decoder.DecodeUint32Varint()  # TODO: verify flags
    regexp = RegExp(pattern=pattern, flags=flags)
    self.objects[next_id] = regexp
    return regexp

  def _ReadJSMap(self) -> Dict[Any, Any]:
    """Reads a Javascript map (dictionary) from the current position.

    Raises:
      errors.ParserError: on an unexpected map length.
    """
    next_id = self._GetNextId()
    js_map = {}

    tag = self._PeekTag()
    while tag != definitions.V8SerializationTag.END_JS_MAP:
      key = self._ReadObject()
      value = self._ReadObject()
      js_map[key] = value
      tag = self._PeekTag()
    self._ConsumeTag(definitions.V8SerializationTag.END_JS_MAP)

    _, expected_length = self.decoder.DecodeUint32Varint()
    if len(js_map) * 2 != expected_length:
      raise errors.ParserError('unexpected length')

    self.objects[next_id] = js_map
    return js_map

  def _ReadJSSet(self) -> Set[Any]:
    """Reads a Javascript set from the current position.

    Raises:
      errors.ParserError: on an unexpected map length.
    """
    next_id = self._GetNextId()

    js_set = set()
    tag = self._PeekTag()
    while tag != definitions.V8SerializationTag.END_JS_SET:
      element = self._ReadObject()
      js_set.add(element)
      tag = self._PeekTag()
    self._ConsumeTag(definitions.V8SerializationTag.END_JS_SET)

    _, expected_length = self.decoder.DecodeUint32Varint()
    if len(js_set) != expected_length:
      raise ValueError('unexpected length')

    self.objects[next_id] = js_set
    return js_set

  def _ReadJSArrayBuffer(
      self, is_shared: bool, is_resizable: bool) -> bytes:
    """Reads a Javascript ArrayBuffer from the current position.

    Args:
      is_shared: True if the buffer is shared, False otherwise.
      is_resizable: True if the buffer is resizable, False otherwise.
    """
    next_id = self._GetNextId()
    array_buffer = b''

    if is_shared:
      raise NotImplementedError('Shared ArrayBuffer not supported yet')

    _, byte_length = self.decoder.DecodeUint32Varint()
    max_byte_length = byte_length
    if is_resizable:
      _, max_byte_length = self.decoder.DecodeUint32Varint()
      if byte_length > max_byte_length:
        self.objects[next_id] = array_buffer
        return array_buffer
    if byte_length:
      _, array_buffer = self.decoder.ReadBytes(byte_length)

    self.objects[next_id] = array_buffer
    return array_buffer

  def _ReadJSArrayBufferView(self, buffer):
    """Reads a JSArrayBufferView from the current position."""
    _, tag = self.decoder.ReadBytes(1)
    _, byte_offset = self.decoder.DecodeUint32Varint()
    _, byte_length = self.decoder.DecodeUint32Varint()

    if self.version >= 14:  # or version_13_broken_data_mode
      _, flags = self.decoder.DecodeUint32Varint()
    else:
      flags = 0

    return ArrayBufferView(
        buffer=buffer,
        tag=definitions.V8ArrayBufferViewTag(tag[0]),
        offset=byte_offset,
        length=byte_length,
        flags=flags)

  def _ReadJSError(self):
    """Reads a Javascript error from the current position."""
    raise NotImplementedError('ValueDeserializer.ReadJSError')

  def _ReadWasmModuleTransfer(self):
    """Reads a Wasm module transfer object from the current position."""
    raise NotImplementedError('ValueDeserializer.ReadWasmModuleTransfer')

  def _ReadWasmMemory(self):
    """Reads a Wasm memory object from the current position."""
    raise NotImplementedError('ValueDeserializer.ReadWasmMemory')

  def ReadSharedObject(self) -> Any:
    """Reads a shared object from the current position."""
    #_, shared_object_id = self.decoder.DecodeUint32Varint()
    raise NotImplementedError('ValueDeserializer.ReadSharedObject')

  def ReadHostObject(self):
    """Reads a Host object using the delegate object.

    Raises:
      errors.ParserError: when the delegate object is None.
    """
    next_id = self._GetNextId()
    if not self.delegate:
      raise errors.ParserError('No delegate to read host object.')
    host_object = self.delegate.ReadHostObject()
    self.objects[next_id] = host_object
    return host_object

  @classmethod
  def FromBytes(cls, data: bytes, delegate: Any) -> Any:
    """Returns a deserialized javascript object from the data.

    Args:
      data: the data to deserialize/parse.
      delegate: an object to delegate parsing additional Javascript objects.

    Returns:
      A python representation of the parsed javascript object.

    Raises:
      errors.ParserError: if there is an invalid V8 javascript header.
    """
    stream = io.BytesIO(data)
    deserializer = cls(stream, delegate)
    if not deserializer.ReadHeader():
      raise errors.ParserError('Invalid V8 header')
    return deserializer.ReadObjectWrapper()
