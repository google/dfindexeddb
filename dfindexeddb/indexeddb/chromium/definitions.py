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
"""Definitions for IndexedDB."""
from enum import Enum, IntEnum, IntFlag


class DatabaseMetaDataKeyType(IntEnum):
  """Database Metadata key types."""
  ORIGIN_NAME = 0
  DATABASE_NAME = 1
  IDB_STRING_VERSION_DATA = 2
  MAX_ALLOCATED_OBJECT_STORE_ID = 3
  IDB_INTEGER_VERSION = 4
  BLOB_NUMBER_GENERATOR_CURRENT_NUMBER = 5
  OBJECT_STORE_META_DATA = 50
  INDEX_META_DATA = 100
  OBJECT_STORE_FREE_LIST = 150
  INDEX_FREE_LIST = 151
  OBJECT_STORE_NAMES = 200
  INDEX_NAMES = 201


class GlobalMetadataKeyType(IntEnum):
  """Global Metadata key types."""
  SCHEMA_VERSION = 0
  MAX_DATABASE_ID = 1
  DATA_VERSION = 2
  RECOVERY_BLOB_JOURNAL = 3
  ACTIVE_BLOB_JOURNAL = 4
  EARLIEST_SWEEP = 5
  EARLIEST_COMPACTION_TIME = 6
  SCOPES_PREFIX = 50
  DATABASE_FREE_LIST = 100
  DATABASE_NAME = 201


class IDBKeyPathType(IntEnum):
  """IndexedDB key path types."""
  NULL = 0
  STRING = 1
  ARRAY = 2


class IDBKeyType(IntEnum):
  """IndexedDB key types."""
  NULL = 0
  STRING = 1
  DATE = 2
  NUMBER = 3
  ARRAY = 4
  MIN_KEY = 5
  BINARY = 6


class IndexMetaDataKeyType(IntEnum):
  """IndexedDB metadata key types."""
  INDEX_NAME = 0
  UNIQUE_FLAG = 1
  KEY_PATH = 2
  MULTI_ENTRY_FLAG = 3


class KeyPrefixType(Enum):
  """IndexedDB key prefix types."""
  GLOBAL_METADATA = 0
  DATABASE_METADATA = 1
  OBJECT_STORE_DATA = 2
  EXISTS_ENTRY = 3
  INDEX_DATA = 4
  INVALID_TYPE = 5
  BLOB_ENTRY = 6


class ObjectStoreMetaDataKeyType(IntEnum):
  """IndexedDB object store metadata key types."""
  OBJECT_STORE_NAME = 0
  KEY_PATH = 1
  AUTO_INCREMENT_FLAG = 2
  IS_EVICTABLE = 3
  LAST_VERSION_NUMBER = 4
  MAXIMUM_ALLOCATED_INDEX_ID = 5
  HAS_KEY_PATH = 6
  KEY_GENERATOR_CURRENT_NUMBER = 7


class ExternalObjectType(IntEnum):
  """IndexedDB external object types."""
  BLOB = 0
  FILE = 1
  FILE_SYSTEM_ACCESS_HANDLE = 2


class BlinkSerializationTag(IntEnum):
  """Blink Javascript serialization tags."""
  MESSAGE_PORT = ord('M')
  MOJO_HANDLE = ord('h')
  BLOB = ord('b')
  BLOB_INDEX = ord('i')
  FILE = ord('f')
  FILE_INDEX = ord('e')
  DOM_FILE_SYSTEM = ord('d')
  FILE_SYSTEM_FILE_HANDLE = ord('n')
  FILE_SYSTEM_DIRECTORY_HANDLE = ord('N')
  FILE_LIST = ord('l')
  FILE_LIST_INDEX = ord('L')
  IMAGE_DATA = ord('#')
  IMAGE_BITMAP = ord('g')
  IMAGE_BITMAP_TRANSFER = ord('G')
  OFFSCREEN_CANVAS_TRANSFER = ord('H')
  READABLE_STREAM_TRANSFER = ord('r')
  TRANSFORM_STREAM_TRANSFER = ord('m')
  WRITABLE_STREAM_TRANSFER = ord('w')
  MEDIA_STREAM_TRACK = ord('s')
  DOM_POINT = ord('Q')
  DOM_POINT_READ_ONLY = ord('W')
  DOM_RECT = ord('E')
  DOM_RECT_READ_ONLY = ord('R')
  DOM_QUAD = ord('T')
  DOM_MATRIX = ord('Y')
  DOM_MATRIX_READ_ONLY = ord('U')
  DOM_MATRIX2D = ord('I')
  DOM_MATRIX2D_READ_ONLY = ord('O')
  CRYPTO_KEY = ord('K')
  RTC_CERTIFICATE = ord('k')
  RTC_ENCODED_AUDIO_FRAME = ord('A')
  RTC_ENCODED_VIDEO_FRAME = ord('V')
  AUDIO_DATA = ord('a')
  VIDEO_FRAME = ord('v')
  ENCODED_AUDIO_CHUNK = ord('y')
  ENCODED_VIDEO_CHUNK = ord('z')
  CROP_TARGET = ord('c')
  RESTRICTION_TARGET = ord('D')
  MEDIA_SOURCE_HANDLE = ord('S')
  DEPRECATED_DETECTED_BARCODE = ord('B')
  DEPRECATED_DETECTED_FACE = ord('F')
  DEPRECATED_DETECTED_TEXT = ord('t')
  FENCED_FRAME_CONFIG = ord('C')
  DOM_EXCEPTION = ord('x')
  TRAILER_OFFSET = 0xFE
  VERSION = 0xFF
  TRAILER_REQUIRES_INTERFACES = 0xA0


class CryptoKeyAlgorithm(IntEnum):
  """CryptoKey Algorithm types."""
  AES_CBC = 1
  HMAC = 2
  RSA_SSA_PKCS1_V1_5 = 3
  SHA1 = 5
  SHA256 = 6
  SHA384 = 7
  SHA512 = 8
  AES_GCM = 9
  RSA_OAEP = 10
  AES_CTR = 11
  AES_KW = 12
  RSA_PSS = 13
  ECDSA = 14
  ECDH = 15
  HKDF = 16
  PBKDF2 = 17
  ED25519 = 18


class NamedCurve(IntEnum):
  """Named Curve types."""
  P256 = 1
  P384 = 2
  P521 = 3


class CryptoKeyUsage(IntFlag):
  """CryptoKey Usage flags."""
  EXTRACTABLE = 1 << 0
  ENCRYPT = 1 << 1
  DECRYPT = 1 << 2
  SIGN = 1 << 3
  VERIFY = 1 << 4
  DERIVE_KEY = 1 << 5
  WRAP_KEY = 1 << 6
  UNWRAP_KEY = 1 << 7
  DRIVE_BITS = 1 << 8


class CryptoKeySubTag(IntEnum):
  """CryptoKey subtag types."""
  AES_KEY = 1
  HMAC_KEY = 2
  RSA_HASHED_KEY = 4
  EC_KEY = 5
  NO_PARAMS_KEY = 6
  ED25519_KEY = 7


class AsymmetricCryptoKeyType(IntEnum):
  """Asymmetric CryptoKey types."""
  PUBLIC_KEY = 1
  PRIVATE_KEY = 2


class WebCryptoKeyType(Enum):
  """WebCryptoKey types."""
  SECRET = 'Secret'
  PUBLIC = 'Public'
  PRIVATE = 'Private'


class V8SerializationTag(IntEnum):
  """V8 Javascript serialization tags."""
  VERSION = 0xFF
  PADDING = ord('\0')
  VERIFY_OBJECT_COUNT = ord('?')
  THE_HOLE = ord('-')
  UNDEFINED = ord('_')
  NULL = ord('0')
  TRUE = ord('T')
  FALSE = ord('F')
  INT32 = ord('I')
  UINT32 = ord('U')
  DOUBLE = ord('N')
  BIGINT = ord('Z')
  UTF8_STRING = ord('S')
  ONE_BYTE_STRING = ord('"')
  TWO_BYTE_STRING = ord('c')
  OBJECT_REFERENCE = ord('^')
  BEGIN_JS_OBJECT = ord('o')
  END_JS_OBJECT = ord('{')
  BEGIN_SPARSE_JS_ARRAY = ord('a')
  END_SPARSE_JS_ARRAY = ord('@')
  BEGIN_DENSE_JS_ARRAY = ord('A')
  END_DENSE_JS_ARRAY = ord('$')
  DATE = ord('D')
  TRUE_OBJECT = ord('y')
  FALSE_OBJECT = ord('x')
  NUMBER_OBJECT = ord('n')
  BIGINT_OBJECT = ord('z')
  STRING_OBJECT = ord('s')
  REGEXP = ord('R')
  BEGIN_JS_MAP = ord(';')
  END_JS_MAP = ord(':')
  BEGIN_JS_SET = ord('\'')
  END_JS_SET = ord(',')
  ARRAY_BUFFER = ord('B')
  RESIZABLE_ARRAY_BUFFER = ord('~')
  ARRAY_BUFFER_TRANSFER = ord('t')
  ARRAY_BUFFER_VIEW = ord('V')
  SHARED_ARRAY_BUFFER = ord('u')
  SHARED_OBJECT = ord('p')
  WASM_MODULE_TRANSFER = ord('w')
  HOST_OBJECT = ord('\\')
  WASM_MEMORY_TRANSFER = ord('m')
  ERROR = ord('r')
  LEGACY_RESERVED_MESSAGE_PORT = ord('M')
  LEGACY_RESERVED_BLOB = ord('b')
  LEGACY_RESERVED_BLOB_INDEX = ord('i')
  LEGACY_RESERVED_FILE = ord('f')
  LEGACY_RESERVED_FILE_INDEX = ord('e')
  LEGACY_RESERVED_DOM_FILE_SYSTEM = ord('d')
  LEGACY_RESERVED_FILE_LIST = ord('l')
  LEGACY_RESERVED_FILE_LIST_INDEX = ord('L')
  LEGACY_RESERVED_IMAGE_DATA = ord('#')
  LEGACY_RESERVED_IMAGE_BITMAP = ord('g')
  LEGACY_RESERVED_IMAGE_BITMAP_TRANSFER = ord('G')
  LEGACY_RESERVED_OFF_SCREEN_CANVAS = ord('H')
  LEGACY_RESERVED_CRYPTO_KEY = ord('K')
  LEGACY_RESERVED_RTC_CERTIFICATE = ord('k')


class V8ArrayBufferViewTag(IntEnum):
  """V8 ArrayBufferView tags."""
  INT8_ARRAY = ord('b')
  UINT8_ARRAY = ord('B')
  UINT8_CLAMPED_ARRAY = ord('C')
  INT16_ARRAY = ord('w')
  UINT16_ARRAY = ord('W')
  INT32_ARRAY = ord('d')
  UINT32_ARRAY = ord('D')
  FLOAT32_ARRAY = ord('f')
  FLOAT64_ARRAY = ord('F')
  BIGINT64_ARRAY = ord('q')
  BIGUINT64_ARRAY = ord('Q')
  DATAVIEW = ord('?')


class V8ErrorTag(IntEnum):
  """V8 Error tags."""
  EVAL_ERROR_PROTOTYPE = ord('E')
  RANGE_ERROR_PROTOTYPE = ord('R')
  REFERENCE_ERROR_PROTOTYPE = ord('F')
  SYNTAX_ERROR_PROTOTYPE = ord('S')
  TYPE_ERROR_PROTOTYPE = ord('T')
  URI_ERROR_PROTOTYPE = ord('U')
  MESSAGE = ord('m')
  CAUSE = ord('c')
  STACK = ord('s')
  END = ord('.')


class ImageSerializationTag(IntEnum):
  """Image Serialization tags."""
  END = 0
  PREDEFINED_COLOR_SPACE = 1
  CANVAS_PIXEL_FORMAT = 2
  IMAGE_DATA_STORAGE_FORMAT = 3
  ORIGIN_CLEAN = 4
  IS_PREMULTIPLIED = 5
  CANVAS_OPACITY_MODE = 6
  PARAMETRIC_COLOR_SPACE = 7
  IMAGE_ORIENTATION = 8
  LAST = IMAGE_ORIENTATION


class SerializedPredefinedColorSpace(IntEnum):
  """Serialized Predefined Color Space enumeration."""
  LEGACY_OBSOLETE = 0
  SRGB = 1
  REC2020 = 2
  P3 = 3
  REC2100HLG = 4
  REC2100PQ = 5
  SRGB_LINEAR = 6
  LAST = SRGB_LINEAR


class SerializedPixelFormat(IntEnum):
  """Serialized Pixel Format enumeration."""
  NATIVE8_LEGACY_OBSOLETE = 0
  F16 = 1
  RGBA8 = 2
  BGRA8 = 3
  RGBX8 = 4
  LAST = RGBX8


class SerializedImageDataStorageFormat(IntEnum):
  """The Serialized Image Data Storage Format."""
  UINT8CLAMPED = 0
  UINT16 = 1
  FLOAT32 = 2
  LAST = FLOAT32


class SerializedOpacityMode(IntEnum):
  """The Serialized Opacity Mode."""
  KNONOPAQUE = 0
  KOPAQUE = 1
  KLAST = KOPAQUE


class SerializedImageOrientation(IntEnum):
  """The Serialized Image Orientation."""
  TOP_LEFT = 0
  TOP_RIGHT = 1
  BOTTOM_RIGHT = 2
  BOTTOM_LEFT = 3
  LEFT_TOP = 4
  RIGHT_TOP = 5
  RIGHT_BOTTOM = 6
  LEFT_BOTTOM = 7
  LAST = LEFT_BOTTOM
