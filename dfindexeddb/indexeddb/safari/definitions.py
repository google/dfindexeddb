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
"""Definitions for Webkit/Safari."""
from enum import IntEnum


CurrentVersion = 0x0000000F  # 15
TerminatorTag = 0xFFFFFFFF
StringPoolTag = 0xFFFFFFFE
NonIndexPropertiesTag = 0xFFFFFFFD
ImageDataPoolTag = 0xFFFFFFFE
StringDataIs8BitFlag = 0x80000000


SIDBKeyVersion = 0x00


class SIDBKeyType(IntEnum):
  """SIDBKeyType."""
  MIN = 0x00
  NUMBER = 0x20
  DATE = 0x40
  STRING = 0x60
  BINARY = 0x80
  ARRAY = 0xA0
  MAX = 0xFF


class SerializationTag(IntEnum):
  """Database Metadata key types.  
  
  All tags are recorded as a single uint8_t.
  """
  ARRAY = 1
  OBJECT = 2
  UNDEFINED = 3
  NULL = 4
  INT = 5
  ZERO = 6
  ONE = 7
  FALSE = 8
  TRUE = 9
  DOUBLE = 10
  DATE = 11
  FILE = 12
  FILE_LIST = 13
  IMAGE_DATA = 14
  BLOB = 15
  STRING = 16
  EMPTY_STRING = 17
  REG_EXP = 18
  OBJECT_REFERENCE = 19
  MESSAGE_PORT_REFERENCE = 20
  ARRAY_BUFFER = 21
  ARRAY_BUFFER_VIEW = 22
  ARRAY_BUFFER_TRANSFER = 23
  TRUE_OBJECT = 24
  FALSE_OBJECT = 25
  STRING_OBJECT = 26
  EMPTY_STRING_OBJECT = 27
  NUMBER_OBJECT = 28
  SET_OBJECT = 29
  MAP_OBJECT = 30
  NON_MAP_PROPERTIES = 31
  NON_SET_PROPERTIES = 32
  CRYPTO_KEY = 33
  SHARED_ARRAY_BUFFER = 34
  WASM_MODULE = 35
  DOM_POINT_READONLY = 36
  DOM_POINT = 37
  DOM_RECT_READONLY = 38
  DOM_RECT = 39
  DOM_MATRIX_READONLY = 40
  DOM_MATRIX = 41
  DOM_QUAD = 42
  IMAGE_BITMAP_TRANSFER = 43
  RTC_CERTIFICATE = 44
  IMAGE_BITMAP = 45
  OFF_SCREEN_CANVAS_TRANSFER = 46
  BIGINT = 47
  BIGINT_OBJECT = 48
  WASM_MEMORY = 49
  RTC_DATA_CHANNEL_TRANSFER = 50
  DOM_EXCEPTION = 51
  WEB_CODECS_ENCODED_VIDEO_CHUNK = 52
  WEB_CODECS_VIDEO_FRAME = 53
  RESIZABLE_ARRAY_BUFFER = 54
  ERROR_INSTANCE = 55
  IN_MEMORY_OFFSCREEN_CANVAS = 56
  IN_MEMORY_MESSAGE_PORT = 57
  WEB_CODECS_ENCODED_AUDIO_CHUNK = 58
  WEB_CODECS_AUDIO_DATA = 59
  MEDIA_STREAM_TRACK = 60
  MEDIA_SOURCE_HANDLE_TRANSFER = 61
  ERROR = 255


class ArrayBufferViewSubtag(IntEnum):
  """ArrayBufferView sub tags."""
  DATA_VIEW = 0
  INT8_ARRAY = 1
  UINT8_ARRAY = 2
  UINT8_CLAMPED_ARRAY = 3
  INT16_ARRAY = 4
  UINT16_ARRAY = 5
  INT32_ARRAY = 6
  UINT32_ARRAY = 7
  FLOAT32_ARRAY = 8
  FLOAT64_ARRAY = 9
  BIG_INT64_ARRAY = 10
  BIG_UINT64_ARRAY = 11
