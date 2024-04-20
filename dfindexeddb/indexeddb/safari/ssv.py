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
"""Parsers for Safari Serialized Script Values."""
from datetime import datetime
from dataclasses import dataclass
import io
from typing import Any, Dict

from dfindexeddb import errors
from dfindexeddb import utils
from dfindexeddb.indexeddb.safari import definitions


@dataclass
class BufferArrayView:
  """A parsed Javascript BufferArrayView."""
  buffer: bytes
  offset: int
  length: int
  flags: int


@dataclass
class FileData:
  """A parsed FileData."""
  path: str
  url: str
  type: str
  name: str
  last_modified: float


@dataclass
class FileList:
  """A parsed FileList."""
  files: list[FileData]


class JSArray(list):
  """A parsed Javascript array.

  This is a wrapper around a standard Python list to allow assigning arbitrary
  properties as is possible in the Javascript equivalent.
  """

  def __repr__(self):
    array_entries = ", ".join([str(entry) for entry in list(self)])
    properties = ", ".join(
        f'{key}: {value}' for key, value in self.properties.items())
    return f'[{array_entries}, {properties}]'

  @property
  def properties(self) -> Dict[str, Any]:
    """Returns the object properties."""
    return self.__dict__

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
  flags: str


@dataclass(frozen=True)
class Undefined:
  """A parsed Javascript undef."""


class SerializedScriptValueDecoder():
  """Decodes a Serialized Script Value from a stream of bytes.

  Attributes:
    decoder: the stream decoder.
  """
  def __init__(self, stream: io.BytesIO):
    self.decoder = utils.StreamDecoder(stream)
    self.version = None
    self.constant_pool = []
    self.object_pool = []

  def PeekTag(self) -> int:
    """Peeks a tag."""
    _, peeked_bytes = self.decoder.PeekBytes(4)
    return int.from_bytes(peeked_bytes, byteorder='little')

  def PeekSerializationTag(self) -> definitions.SerializationTag:
    """Peeks a SerializationTag."""
    offset, terminal_byte = self.decoder.PeekBytes(1)
    try:
      return definitions.SerializationTag(terminal_byte[0])
    except ValueError as error:
      raise errors.ParserError(
          f'Invalid terminal {terminal_byte} at offset {offset}') from error

  def DecodeSerializationTag(self) -> tuple[int, definitions.SerializationTag]:
    """Decodes a SerializationTag."""
    offset, terminal_byte = self.decoder.DecodeUint8()
    try:
      return offset, definitions.SerializationTag(terminal_byte)
    except ValueError as error:
      raise errors.ParserError(
          f'Invalid terminal {terminal_byte} at offset {offset}') from error

  def DecodeArray(self) -> JSArray:
    """ Decodes an Array value."""
    _, length = self.decoder.DecodeUint32()
    array = JSArray()
    for _ in range(length):
      _, _ = self.decoder.DecodeUint32()
      _, value = self.DecodeValue()
      array.append(value)

    offset, terminator_tag = self.decoder.DecodeUint32()
    if terminator_tag != definitions.TerminatorTag:
      raise errors.ParserError(f'Terminator tag not found at offset {offset}.')

    _, tag = self.decoder.DecodeUint32()
    if tag == definitions.NonIndexPropertiesTag:
      while tag != definitions.TerminatorTag:
        name = self.DecodeStringData()
        _, value = self.DecodeValue()
        _, tag = self.decoder.DecodeUint32()
        array.properties[name] = value
    elif tag != definitions.TerminatorTag:
      raise errors.ParserError(f'Terminator tag not found at offset {offset}.')
    return array

  def DecodeObject(self) -> Dict[str, Any]:
    """Decodes an Object value."""
    tag = self.PeekTag()
    js_object = {}
    while tag != definitions.TerminatorTag:
      name = self.DecodeStringData()
      _, value = self.DecodeValue()
      js_object[name] = value
      tag = self.PeekTag()
    _ = self.decoder.DecodeUint32()

    return js_object

  def DecodeStringData(self) -> str:
    """Decodes a StringData value."""
    peeked_tag = self.PeekTag()
    if peeked_tag == definitions.TerminatorTag:
      raise errors.ParserError('TerminatorTag found')

    if peeked_tag == definitions.StringPoolTag:
      _ = self.decoder.DecodeUint32()
      if len(self.constant_pool) < 0xff:
        _, cp_index = self.decoder.DecodeUint8()
      elif len(self.constant_pool) < 0xffff:
        _, cp_index = self.decoder.DecodeUint16()
      elif len(self.constant_pool) < 0xffffffff:
        _, cp_index = self.decoder.DecodeUint32()
      else:
        raise errors.ParserError('Unexpected constant pool size')
      return self.constant_pool[cp_index]

    _, is_8bit_length = self.decoder.DecodeUint32()
    if is_8bit_length == definitions.TerminatorTag:
      raise errors.ParserError('Disallowed string length found.')

    length = is_8bit_length & 0x7FFFFFFF
    is_8bit = is_8bit_length & definitions.StringDataIs8BitFlag
    _, characters = self.decoder.ReadBytes(length)
    if is_8bit:
      value = characters.decode('latin-1')
    else:
      value = characters.decode('utf-16-le')
    self.constant_pool.append(value)
    return value

  def DecodeDate(self) -> datetime:
    """Decodes a Date value."""
    _, timestamp = self.decoder.DecodeDouble()
    value = datetime.utcfromtimestamp(timestamp/1000)
    return value

  def DecodeFileData(self):
    """Decodes a FileData value."""
    path = self.DecodeStringData()
    url = self.DecodeStringData()
    file_type = self.DecodeStringData()
    name = self.DecodeStringData()
    _, last_modified = self.decoder.DecodeDouble()

    return FileData(
        path=path,
        url=url,
        type=file_type,
        name=name,
        last_modified=last_modified)

  def DecodeFileList(self):
    """Decodes a FileList value."""
    _, length = self.decoder.DecodeUint32()
    file_list = []
    for _ in range(length):
      file_list.append(self.DecodeFileData())
    return FileList(files=file_list)

  def DecodeImageData(self):
    """Decodes an ImageData value."""
    _, width = self.decoder.DecodeUint32()
    _, height = self.decoder.DecodeUint32()
    _, length = self.decoder.DecodeUint32()
    data = self.decoder.ReadBytes(length)

    if self.version > 7:
      _, color_space = self.decoder.DecodeUint8()
    else:
      color_space = None

    return {
      'width': width,
      'height': height,
      'length': length,
      'data': data,
      'color_space': color_space
    }

  def DecodeBlob(self):
    """Decodes a Blob value."""
    url = self.DecodeStringData()
    blob_type = self.DecodeStringData()
    size = self.decoder.DecodeUint64()
    if self.version >= 11:
      _, memory_cost = self.decoder.DecodeUint64()
    else:
      memory_cost = None

    return {
      'url': url,
      'blob_type': blob_type,
      'size': size,
      'memory_cost': memory_cost
    }

  def DecodeRegExp(self) -> RegExp:
    """Decodes a RegExp value."""
    pattern = self.DecodeStringData()
    flags = self.DecodeStringData()
    return RegExp(pattern=pattern, flags=flags)

  def DecodeMapData(self) -> dict:
    """Decodes a Map value."""
    tag = self.PeekSerializationTag()
    js_map = {}

    while tag != definitions.SerializationTag.NON_MAP_PROPERTIES:
      _, key = self.DecodeValue()
      _, value = self.DecodeValue()
      js_map[key] = value
      tag = self.PeekSerializationTag()

    # consume the NonMapPropertiesTag
    _, tag = self.DecodeSerializationTag()

    pool_tag = self.PeekTag()
    while pool_tag != definitions.TerminatorTag:
      name = self.DecodeStringData()
      value = self.DecodeValue()
      js_map[name] = value  # TODO
      pool_tag = self.PeekTag()

    _, tag = self.decoder.DecodeUint32()

    return js_map

  def DecodeSetData(self) -> set:
    """Decodes a SetData value."""
    tag = self.PeekSerializationTag()
    js_set = set()

    while tag != definitions.SerializationTag.NON_SET_PROPERTIES:
      _, key = self.DecodeValue()
      js_set.add(key)
      tag = self.PeekSerializationTag()

    # consume the NonSetPropertiesTag
    _, tag = self.DecodeSerializationTag()

    pool_tag = self.PeekTag()
    while pool_tag != definitions.TerminatorTag:
      name = self.DecodeStringData()
      value = self.DecodeValue()
      js_set.__dict__[name] = value
      pool_tag = self.decoder.PeekBytes(4)

    # consume the TerminatorTag
    _, tag = self.decoder.DecodeUint32()
    return js_set

  def DecodeCryptoKey(self) -> Any:
    """Decodes a CryptoKey value."""
    _, wrapped_key_length = self.decoder.DecodeUint64()
    _, wrapped_key = self.decoder.ReadBytes(wrapped_key_length)
    return wrapped_key

  def DecodeBigIntData(self):
    """Decodes a BigIntData value."""
    _, sign = self.decoder.DecodeUint8()
    _, number_of_elements = self.decoder.DecodeUint32()
    contents = []
    for _ in range(number_of_elements):
      _, element = self.decoder.ReadBytes(8)
      contents.extend(element)
    value = int.from_bytes(contents, byteorder='little', signed=bool(sign))
    return value

  def DecodeArrayBuffer(self):
    """Decodes an ArrayBuffer value."""
    _, byte_length = self.decoder.DecodeUint64()
    _, buffer = self.decoder.ReadBytes(byte_length)
    self.object_pool.append(buffer)
    return buffer

  def DecodeResizableArrayBuffer(self):
    """Decodes an ArrayBuffer value."""
    _, byte_length = self.decoder.DecodeUint64()
    _, _max_length = self.decoder.DecodeUint64()  # TODO: include this value.
    _, buffer = self.decoder.ReadBytes(byte_length)
    self.object_pool.append(buffer)
    return buffer

  def DecodeArrayBufferTransfer(self):
    """Decodes an ArrayBufferTransfer value."""
    _, value = self.decoder.DecodeUint32()
    return value

  def DecodeSharedArrayBuffer(self):
    """Decodes an SharedArrayBuffer value."""
    _, value = self.decoder.DecodeUint32()
    return value

  def DecodeObjectReference(self):
    """Decodes an ObjectReference value."""
    _, object_ref = self.decoder.DecodeUint8()
    return self.object_pool[object_ref - 1]

  def DecodeArrayBufferView(self):
    """Decodes an ArrayBufferView value."""
    _, array_buffer_view_subtag = self.decoder.DecodeUint8()
    array_buffer_view_subtag = definitions.ArrayBufferViewSubtag(
        array_buffer_view_subtag)
    _, byte_offset = self.decoder.DecodeUint64()
    _, byte_length = self.decoder.DecodeUint64()
    _, next_serialization_tag = self.DecodeSerializationTag()

    if next_serialization_tag == definitions.SerializationTag.ARRAY_BUFFER:
      value = self.DecodeArrayBuffer()
    elif (next_serialization_tag ==
          definitions.SerializationTag.OBJECT_REFERENCE):
      value = self.DecodeObjectReference()
    else:
      raise errors.ParserError(
          f'Unexpected serialization tag {next_serialization_tag}.')
    return value[byte_offset:byte_offset+byte_length]

  def DecodeSerializedValue(self) -> Any:
    """Decodes a serialized value.

    Returns:
      the serialized value.

    Raises:
      ParserError: when CurrentVersion is not found.
    """
    _, current_version = self.decoder.DecodeUint32()
    if current_version != definitions.CurrentVersion:
      raise errors.ParserError(
          f'{current_version} is not the expected CurrentVersion')
    _, value = self.DecodeValue()
    return value

  def DecodeValue(self) -> tuple[int, Any]:
    """Decodes a value."""
    offset, tag = self.DecodeSerializationTag()
    if tag == definitions.SerializationTag.ARRAY:
      value = self.DecodeArray()
    elif tag == definitions.SerializationTag.OBJECT:
      value = self.DecodeObject()
    if tag == definitions.SerializationTag.UNDEFINED:
      value = Undefined()
    elif tag == definitions.SerializationTag.NULL:
      value = Null()
    elif tag == definitions.SerializationTag.INT:
      _, value = self.decoder.DecodeInt32()
    elif tag == definitions.SerializationTag.ZERO:
      value = 0
    elif tag == definitions.SerializationTag.ONE:
      value = 1
    elif tag == definitions.SerializationTag.FALSE:
      value = False
    elif tag == definitions.SerializationTag.TRUE:
      value = True
    elif tag == definitions.SerializationTag.DOUBLE:
      _, value = self.decoder.DecodeDouble()
    elif tag == definitions.SerializationTag.DATE:
      value = self.DecodeDate()
    elif tag == definitions.SerializationTag.FILE:
      value = self.DecodeFileData()
    elif tag == definitions.SerializationTag.FILE_LIST:
      value = self.DecodeFileList()
    elif tag == definitions.SerializationTag.IMAGE_DATA:
      value = self.DecodeImageData()
    elif tag == definitions.SerializationTag.BLOB:
      value = self.DecodeBlob()
    elif tag == definitions.SerializationTag.STRING:
      value = self.DecodeStringData()
    elif tag == definitions.SerializationTag.EMPTY_STRING:
      value = ''
    elif tag == definitions.SerializationTag.REG_EXP:
      value = self.DecodeRegExp()
    elif tag == definitions.SerializationTag.OBJECT_REFERENCE:
      value = self.DecodeObjectReference()
    # elif tag == definitions.SerializationTag.MESSAGE_PORT_REFERENCE:
    #   value = self.DecodeMessagePortReference()
    elif tag == definitions.SerializationTag.ARRAY_BUFFER:
      value = self.DecodeArrayBuffer()
    elif tag == definitions.SerializationTag.ARRAY_BUFFER_VIEW:
      value = self.DecodeArrayBufferView()
    elif tag == definitions.SerializationTag.ARRAY_BUFFER_TRANSFER:
      value = self.DecodeArrayBufferTransfer()
    elif tag == definitions.SerializationTag.TRUE_OBJECT:
      self.object_pool.append(True)
      value = True
    elif tag == definitions.SerializationTag.FALSE_OBJECT:
      self.object_pool.append(False)
      value = False
    elif tag == definitions.SerializationTag.STRING_OBJECT:
      value = self.DecodeStringData()
      self.object_pool.append(value)
    elif tag == definitions.SerializationTag.EMPTY_STRING_OBJECT:
      value = ''
      self.object_pool.append(value)
    elif tag == definitions.SerializationTag.NUMBER_OBJECT:
      _, value = self.decoder.DecodeDouble()
      self.object_pool.append(value)
    elif tag == definitions.SerializationTag.SET_OBJECT:
      value = self.DecodeSetData()
    elif tag == definitions.SerializationTag.MAP_OBJECT:
      value = self.DecodeMapData()
    elif tag == definitions.SerializationTag.CRYPTO_KEY:
      value = self.DecodeCryptoKey()
    elif tag == definitions.SerializationTag.SHARED_ARRAY_BUFFER:
      value = self.DecodeSharedArrayBuffer()
    # elif tag == definitions.SerializationTag.WASM_MODULE:
    #   _, value = self.DecodeWasmModule()
    # elif tag == definitions.SerializationTag.DOM_POINT_READONLY:
    #   _, value = self.DecodeDOMPoint()
    # elif tag == definitions.SerializationTag.DOM_POINT:
    #   _, value = self.DecodeDOMPoint()
    # elif tag == definitions.SerializationTag.DOM_RECT_READONLY:
    #   _, value = self.DecodeDOMRect()
    # elif tag == definitions.SerializationTag.DOM_RECT:
    #   _, value = self.DecodeDOMRect()
    # elif tag == definitions.SerializationTag.DOM_MATRIX_READONLY:
    #   _, value = self.DecodeDOMMatrix()
    # elif tag == definitions.SerializationTag.DOM_MATRIX:
    #   _, value = self.DecodeDOMMatrix()
    # elif tag == definitions.SerializationTag.DOM_QUAD:
    #   _, value = self.DecodeDOMQuad()
    # elif tag == definitions.SerializationTag.IMAGE_BITMAP_TRANSFER:
    #   _, value = self.DecodeImageBitmapTransferTag()
    # elif tag == definitions.SerializationTag.RTC_CERTIFICATE:
    #   _, value = self.DecodeRTCCCertificate()
    # elif tag == definitions.SerializationTag.IMAGE_BITMAP:
    #   _, value = self.DecodeImageBitmap()
    # elif tag == definitions.SerializationTag.OFF_SCREEN_CANVAS_TRANSFER:
    #   _, value = self.DecodeOffscreenCanvasTransferTag()
    elif tag == definitions.SerializationTag.BIGINT:
      value = self.DecodeBigIntData()
    elif tag == definitions.SerializationTag.BIGINT_OBJECT:
      value = self.DecodeBigIntData()
      self.object_pool.append(value)
    # elif tag == definitions.SerializationTag.WASM_MEMORY:
    #   _, value = self.DecodeWasmMemory()
    # elif tag == definitions.SerializationTag.RTC_DATA_CHANNEL_TRANSFER:
    #   _, value = self.DecodeRTCDataChannel()
    # elif tag == definitions.SerializationTag.DOM_EXCEPTION:
    #   _, value = self.DecodeDOMException()
    # elif tag == definitions.SerializationTag.WEB_CODECS_ENCODED_VIDEO_CHUNK:
    #   _, value = self.DecodeWebCodecsEncodedVideoChunk()
    # elif tag == definitions.SerializationTag.WEB_CODECS_VIDEO_FRAME:
    #   _, value = self.DecodeWebCodecsVideoFrame()
    # elif tag == definitions.SerializationTag.RESIZABLE_ARRAY_BUFFER:
    #   value = self.DecodeResizableArrayBuffer()
    # elif tag == definitions.SerializationTag.ERROR_INSTANCE:
    #   _, value = self.DecodeErrorInstanceTag()
    # elif tag == definitions.SerializationTag.IN_MEMORY_OFFSCREEN_CANVAS:
    #   _, value = self.DecodeInMemoryOffscreenCanvas()
    # elif tag == definitions.SerializationTag.IN_MEMORY_MESSAGE_PORT:
    #   _, value = self.DecodeInMemoryOffscreenCanvas()
    # elif tag == definitions.SerializationTag.WEB_CODECS_ENCODED_AUDIO_CHUNK:
    #   _, value = self.DecodeWebCodecsEncodedAudioChunk()
    # elif tag == definitions.SerializationTag.WEB_CODECS_AUDIO_DATA:
    #   _, value = self.DecodeWebCodecsAudioData()
    # elif tag == definitions.SerializationTag.MEDIA_STREAM_TRACK:
    #   _, value = self.DecodeMediaStreamTrack()
    # elif tag == definitions.SerializationTag.MEDIA_SOURCE_HANDLE_TRANSFER:
    #   _, value = self.DecodeMediaSourceHandle()
    return offset, value

  @classmethod
  def FromBytes(cls, data: bytes) -> Any:
    """Returns a deserialized javascript object from the data.

    Args:
      data: the data to deserialize/parse.

    Returns:
      A python representation of the parsed javascript object.

    Raises:
      errors.ParserError: if there is an invalid V8 javascript header.
    """
    stream = io.BytesIO(data)
    deserializer = cls(stream)
    return deserializer.DecodeSerializedValue()
