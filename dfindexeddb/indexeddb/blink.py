"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# -*- coding: utf-8 -*-
"""Parsers for blink javascript serialized objects."""
import io
from typing import Any

from dfindexeddb import utils
from dfindexeddb.indexeddb import definitions
from dfindexeddb.indexeddb import v8



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
      trailer_offset_data_size = 1 + 8 + 4 # 1 + sizeof(uint64) + sizeof(uint32)
      consumed_bytes += trailer_offset_data_size
      if consumed_bytes >= len(self.raw_data):
        return 0
    return consumed_bytes

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
    raise NotImplementedError(f'V8ScriptValueDecoder.ReadHostObject - {tag}')

  def Deserialize(self) -> Any:
    """Deserializes a Blink SSV.

    The serialization format has two 'envelopes'.
    [version tag] [Blink version] [version tag] [v8 version] ...

    Returns:
      The deserialized script value.
    """
    version_envelope_size = self._ReadVersionEnvelope()
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
