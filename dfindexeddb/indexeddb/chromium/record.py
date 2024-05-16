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
"""Parses Chromium IndexedDb structures."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import io
import pathlib
import sys
import traceback
from typing import Any, BinaryIO, Generator, Optional, Tuple, Type, TypeVar, \
    Union

from dfindexeddb import errors
from dfindexeddb.indexeddb.chromium import blink
from dfindexeddb.indexeddb.chromium import definitions
from dfindexeddb.leveldb import record
from dfindexeddb.leveldb import utils


T = TypeVar('T')


@dataclass
class KeyPrefix(utils.FromDecoderMixin):
  """The IndexedDB key prefix.

  Attributes:
    offset: the offset of the key prefix.
    database_id: the database ID.
    object_store_id: the object store ID.
    index_id: the index ID.
  """
  offset: int = field(compare=False)
  database_id: int
  object_store_id: int
  index_id: int

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0) -> KeyPrefix:
    """Decodes a KeyPrefix from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      the decoded KeyPrefix.

    Raises:
      ParserError: when there is an invalid database/object store/index ID
        length.
    """
    offset, raw_prefix = decoder.ReadBytes(1)

    database_id_length = (raw_prefix[0] & 0xE0 >> 5) + 1
    object_store_id_length = (raw_prefix[0] & 0x1C >> 2) + 1
    index_id_length = (raw_prefix[0] & 0x03) + 1

    if database_id_length < 1 or database_id_length > 8:
      raise errors.ParserError('Invalid database ID length')

    if object_store_id_length < 1 or object_store_id_length > 8:
      raise errors.ParserError('Invalid object store ID length')

    if index_id_length < 1 or index_id_length > 4:
      raise errors.ParserError('Invalid index ID length')

    _, database_id = decoder.DecodeInt(database_id_length)
    _, object_store_id = decoder.DecodeInt(object_store_id_length)
    _, index_id = decoder.DecodeInt(index_id_length)

    return cls(
        offset=base_offset + offset,
        database_id=database_id,
        object_store_id=object_store_id,
        index_id=index_id)

  def GetKeyPrefixType(self) -> definitions.KeyPrefixType:
    """Returns the KeyPrefixType.

    The KeyPrefixType is based on the database/object store/index ID values.

    Raises:
      ParserError: if the key prefix is unknown.
    """
    if not self.database_id:
      return definitions.KeyPrefixType.GLOBAL_METADATA
    if not self.object_store_id:
      return definitions.KeyPrefixType.DATABASE_METADATA
    if self.index_id == 1:
      return definitions.KeyPrefixType.OBJECT_STORE_DATA
    if self.index_id == 2:
      return definitions.KeyPrefixType.EXISTS_ENTRY
    if self.index_id == 3:
      return definitions.KeyPrefixType.BLOB_ENTRY
    if self.index_id >= 30:
      return definitions.KeyPrefixType.INDEX_DATA
    raise errors.ParserError(
        f'Unknown KeyPrefixType (index_id={self.index_id})')


@dataclass
class IDBKey(utils.FromDecoderMixin):
  """An IDBKey.

  Attributes:
    offset: the offset of the IDBKey.
    type: the type of the IDBKey.
    value: the value of the IDBKey.
  """
  offset: int = field(compare=False)
  type: definitions.IDBKeyType
  value: Union[list, bytes, str, float, datetime, None]

  _MAXIMUM_DEPTH = 2000

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      base_offset: int = 0  #pylint: disable=unused-argument
  ) -> IDBKey:
    """Decodes an IDBKey from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder
      base_offset: the base offset.

    Returns:
      An IDBKey

    Raises:
      ParserError: on invalid IDBKeyType or invalid array length during
        parsing.
      RecursionError: if maximum depth encountered during parsing.
    """

    def RecursiveParse(depth: int) -> Tuple[
        int, definitions.IDBKeyType, Union[
            list, bytes, str, float, datetime, None]]:
      """Recursively parses IDBKeys.

      Args:
        depth: the current recursion depth.

      Returns:
        A tuple of the offset, the key type and the key value (where the value
          can be bytes, str, float, datetime or a list of these types).

      Raises:
        ParserError: on invalid IDBKeyType or invalid array length during
          parsing.
        RecursionError: if maximum depth encountered during parsing.
      """
      if depth == cls._MAXIMUM_DEPTH:
        raise RecursionError('Maximum recursion depth encountered during parse')
      offset, key_type_value = decoder.DecodeInt(1)
      key_type = definitions.IDBKeyType(key_type_value)

      if key_type == definitions.IDBKeyType.NULL:
        value = None
      elif key_type == definitions.IDBKeyType.ARRAY:
        _, length = decoder.DecodeVarint()
        if length < 0:
          raise errors.ParserError('Invalid length encountered')
        value = []
        while length:
          entry = RecursiveParse(depth + 1)
          value.append(entry[2])
          length -= 1
      elif key_type == definitions.IDBKeyType.BINARY:
        _, value = decoder.DecodeBlobWithLength()
      elif key_type == definitions.IDBKeyType.STRING:
        _, value = decoder.DecodeStringWithLength()
      elif key_type == definitions.IDBKeyType.DATE:
        _, raw_value = decoder.DecodeDouble()
        value = datetime.utcfromtimestamp(raw_value/1000.0)
      elif key_type == definitions.IDBKeyType.NUMBER:
        _, value = decoder.DecodeDouble()
      elif key_type == definitions.IDBKeyType.MIN_KEY:
        value = None
      else:
        raise errors.ParserError('Invalid IndexedDbKeyType')
      return offset, key_type, value

    offset, key_type, value = RecursiveParse(0)
    return cls(base_offset + offset, key_type, value)


@dataclass
class IDBKeyPath(utils.FromDecoderMixin):
  """An IDBKeyPath.

  Arguments:
    offset: the offset of the IDBKeyPath.
    type: the IDBKeyPath type.
    value: the IDBKeyPath value.
  """
  offset: int = field(compare=False)
  type: definitions.IDBKeyPathType
  value: Union[str, list[str], None]

  @classmethod
  def FromDecoder(cls, decoder: utils.LevelDBDecoder,
                   base_offset: int = 0) -> IDBKeyPath:
    """Decodes an IDBKeyPath from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      An IDBKeyPath

    Raises:
      ParserError: on insufficient bytes or invalid array length during
        parsing.
    """
    buffer = decoder.stream.getvalue()  #pytype: disable=attribute-error
    if len(buffer) < 3:
      raise errors.ParserError('Insufficient bytes to parse.')

    if buffer[0:2] != b'\x00\x00':
      offset, value = decoder.DecodeString()
      return IDBKeyPath(offset, definitions.IDBKeyPathType.STRING, value)

    _, type_bytes = decoder.ReadBytes(3)
    key_path_type_byte = type_bytes[2]
    key_path_type = definitions.IDBKeyPathType(key_path_type_byte)

    if key_path_type == definitions.IDBKeyPathType.NULL:
      value = None
      offset = decoder.stream.tell()
    elif key_path_type == definitions.IDBKeyPathType.STRING:
      offset, value = decoder.DecodeStringWithLength()
    elif key_path_type == definitions.IDBKeyPathType.ARRAY:
      value = []
      offset, count = decoder.DecodeVarint()
      if count < 0:
        raise errors.ParserError(f'Invalid array length {count}')
      for _ in range(count):
        _, entry = decoder.DecodeStringWithLength()
        value.append(entry)
    return IDBKeyPath(base_offset + offset, key_path_type, value)


@dataclass
class BlobJournalEntry(utils.FromDecoderMixin):
  """A blob journal entry.

  Attributes:
    offset (int): the offset.
    database_id (int): the database ID.
    blob_number (int): the blob number.
  """
  offset: int = field(compare=False)
  database_id: int
  blob_number: int

  @classmethod
  def FromDecoder(cls, decoder: utils.LevelDBDecoder,
                   base_offset: int = 0) -> BlobJournalEntry:
    """Decodes a BlobJournalEntry from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      A BlobJournalEntry.
    """
    offset, database_id = decoder.DecodeUint64Varint()
    _, blob_number = decoder.DecodeUint64Varint()
    return cls(offset=base_offset + offset, database_id=database_id,
               blob_number=blob_number)


@dataclass
class BlobJournal(utils.FromDecoderMixin):
  """A BlobJournal.

  Attributes:
    offset (int): the offset.
    entries (list[BlobJournalEntry]): the list of blob journal entries.
  """
  offset: int = field(compare=False)
  entries: list[BlobJournalEntry]

  @classmethod
  def FromDecoder(cls, decoder: utils.LevelDBDecoder,
                   base_offset: int = 0) -> BlobJournal:
    """Decodes a BlobJournal from the current position of a LevelDBDecoder.

    Blob journals are zero-or-more instances of BlobJournalEntry.  There is no
    length prefix; just read until you run out of data.

    Ref: indexeddb_db_leveldb_coding.cc#DecodeBlobJournal

    Args:
      decoder: the LevelDBDecoder
      base_offset: the base offset.

    Returns:
      A BlobJournal
    """
    offset = decoder.stream.tell()
    entries = []

    # since there is no length prefix, consume the remaining buffer
    while True:
      try:
        journal_entry = BlobJournalEntry.FromDecoder(decoder, base_offset)
      except errors.DecoderError:
        break
      entries.append(journal_entry)

    return cls(offset=base_offset + offset, entries=entries)


@dataclass
class BaseIndexedDBKey:
  """A base class for IndexedDB coded leveldb keys and values.

  This class provides an interface to parse the key (using from_bytes/
  from_stream/from_decoder) and the value (using parse_value/decode_value).

  Attributes:
    offset: the offset of the key (after the key_prefix).
    key_prefix: the key prefix.
  """
  offset: int
  key_prefix: KeyPrefix

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> Any:
    """Decodes the value from the current position of the LevelDBDecoder.

    To be implemented by subclasses.

    Args:
      decoder: the stream decoder

    Raises:
      NotImplementedError.
    """
    raise NotImplementedError(f'{self.__class__.__name__}.decode_value')

  def ParseValue(self, value_data: bytes) -> Any:
    """Parses the value from raw bytes.

    Args:
      value_data: the raw value bytes.

    Returns:
      The parsed value.
    """
    if not value_data:
      return None
    decoder = utils.LevelDBDecoder(io.BytesIO(value_data))
    return self.DecodeValue(decoder)

  @classmethod
  def FromDecoder(
      cls: T,
      decoder: utils.LevelDBDecoder,
      key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> T:  #pylint: disable=unused-variable
    """Decodes the remaining key data from the current decoder position.

    Args:
      decoder: the stream decoder.
      key_prefix: the decoded key_prefix.
      base_offset: the base offset.

    Returns:
      The decoded key.

    Raises:
      NotImplementedError.
    """
    raise NotImplementedError(f'{cls.__class__.__name__}.decode_key')

  @classmethod
  def FromStream(
      cls: Type[T], stream: BinaryIO, base_offset: int = 0) -> T:
    """Parses the key from the current position of the binary stream.

    Args:
      stream: the binary stream.
      base_offset: the base offset of the stream.

    Returns:
      The decoded key.
    """
    decoder = utils.LevelDBDecoder(stream)
    key_prefix = KeyPrefix.FromDecoder(decoder, base_offset=base_offset)
    return cls.FromDecoder(
        decoder=decoder, key_prefix=key_prefix, base_offset=base_offset)

  @classmethod
  def FromBytes(
      cls: Type[T], raw_data: bytes, base_offset: int = 0) -> T:
    """Parses the key from the raw key bytes.

    Args:
      raw_data: the raw key data.
      base_offset: the base offset of the key data.

    Returns:
      The decoded key.
    """
    stream = io.BytesIO(raw_data)
    return cls.FromStream(stream=stream, base_offset=base_offset)


@dataclass
class SchemaVersionKey(BaseIndexedDBKey):
  """A schema version IndexedDb key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the schema version value."""
    return decoder.DecodeVarint()[1]

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> SchemaVersionKey:
    """Decodes the schema version key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.SCHEMA_VERSION:
      raise errors.ParserError('Not a SchemaVersionKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class MaxDatabaseIdKey(BaseIndexedDBKey):
  """A max database ID IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the maximum database value."""
    return decoder.DecodeVarint()[1]

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> MaxDatabaseIdKey:
    """Decodes the maximum database key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.MAX_DATABASE_ID:
      raise errors.ParserError('Not a MaxDatabaseIdKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class DataVersionKey(BaseIndexedDBKey):
  """A data version IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the data version value."""
    return decoder.DecodeUint64Varint()[1]

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> DataVersionKey:
    """Decodes the data version key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.DATA_VERSION:
      raise errors.ParserError('Not a DataVersionKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class RecoveryBlobJournalKey(BaseIndexedDBKey):
  """A recovery blob journal IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> BlobJournal:
    """Decodes the recovery blob journal value."""
    return BlobJournal.FromDecoder(decoder)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> RecoveryBlobJournalKey:
    """Decodes the recovery blob journal key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.RECOVERY_BLOB_JOURNAL:
      raise errors.ParserError('Not a RecoveryBlobJournalKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class ActiveBlobJournalKey(BaseIndexedDBKey):
  """An active blob journal IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> BlobJournal:
    """Decodes the active blob journal value."""
    return BlobJournal.FromDecoder(decoder)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> ActiveBlobJournalKey:
    """Decodes the active blob journal value."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.ACTIVE_BLOB_JOURNAL:
      raise errors.ParserError('Not a ActiveBlobJournalKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class EarliestSweepKey(BaseIndexedDBKey):
  """An earliest sweep IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the earliest sweep value."""
    _, data = decoder.ReadBytes()
    return int.from_bytes(data, byteorder='little', signed=False)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> EarliestSweepKey:
    """Decodes the earliest sweep value."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.EARLIEST_SWEEP:
      raise errors.ParserError('Not a EarliestSweepKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class EarliestCompactionTimeKey(BaseIndexedDBKey):
  """An earliest compaction time IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the earliest compaction time value."""
    _, data = decoder.ReadBytes()
    return int.from_bytes(data, byteorder='little', signed=False)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> EarliestCompactionTimeKey:
    """Decodes the earliest compaction time key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.EARLIEST_COMPACTION_TIME:
      raise errors.ParserError('Not a EarliestCompactionTimeKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class ScopesPrefixKey(BaseIndexedDBKey):
  """A scopes prefix IndexedDB key."""

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> Optional[bytes]:
    """Decodes the scopes prefix value."""
    if decoder.NumRemainingBytes:
      return decoder.ReadBytes()[1]
    return None

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> ScopesPrefixKey:
    """Decodes the scopes prefix key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.SCOPES_PREFIX:
      raise errors.ParserError('Not a ScopesPrefixKey')
    return cls(offset=base_offset + offset, key_prefix=key_prefix)


@dataclass
class DatabaseFreeListKey(BaseIndexedDBKey):
  """A database free list IndexedDB key.

  Attributes:
    database_id: the database ID.
  """
  database_id: int

  def DecodeValue(self, decoder: utils.LevelDBDecoder):
    """Decodes the database free list value."""
    raise NotImplementedError('DatabaseFreeListKey.decode_value')

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> DatabaseFreeListKey:
    """Decodes the database free list key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.DATABASE_FREE_LIST:
      raise errors.ParserError('Not a DatabaseFreeListKey')
    _, database_id = decoder.DecodeVarint()
    return cls(
        offset=base_offset + offset, key_prefix=key_prefix,
        database_id=database_id)


@dataclass
class DatabaseNameKey(BaseIndexedDBKey):
  """A database name key.

  Attributes:
    origin: the origin of the database.
    database_name: the database name.
  """
  origin: str
  database_name: str

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the database name value.

    The value is the corresponding database ID.
    """
    return decoder.DecodeVarint()[1]

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> DatabaseNameKey:
    """Decodes the database name key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.GlobalMetadataKeyType.DATABASE_NAME:
      raise errors.ParserError('Not a DatabaseNameKey')
    _, origin = decoder.DecodeStringWithLength()
    _, database_name = decoder.DecodeStringWithLength()
    return cls(
        offset=base_offset + offset, key_prefix=key_prefix, origin=origin,
        database_name=database_name)


@dataclass
class GlobalMetaDataKey(BaseIndexedDBKey):
  """A GlobalMetaDataKey parser."""

  METADATA_TYPE_TO_CLASS = {
      definitions.GlobalMetadataKeyType
          .SCHEMA_VERSION: SchemaVersionKey,
      definitions.GlobalMetadataKeyType
          .MAX_DATABASE_ID: MaxDatabaseIdKey,
      definitions.GlobalMetadataKeyType
          .DATA_VERSION: DataVersionKey,
      definitions.GlobalMetadataKeyType
          .RECOVERY_BLOB_JOURNAL: RecoveryBlobJournalKey,
      definitions.GlobalMetadataKeyType
          .ACTIVE_BLOB_JOURNAL: ActiveBlobJournalKey,
      definitions.GlobalMetadataKeyType
          .EARLIEST_SWEEP: EarliestSweepKey,
      definitions.GlobalMetadataKeyType
          .EARLIEST_COMPACTION_TIME: EarliestCompactionTimeKey,
      definitions.GlobalMetadataKeyType
          .SCOPES_PREFIX: ScopesPrefixKey,
      definitions.GlobalMetadataKeyType
          .DATABASE_FREE_LIST: DatabaseFreeListKey,
      definitions.GlobalMetadataKeyType
          .DATABASE_NAME: DatabaseNameKey}

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> Any:
    """Decodes the value from the current position of the LevelDBDecoder.

    Args:
      decoder: the stream decoder
    """

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> Union[Type[ActiveBlobJournalKey],
             Type[DataVersionKey],
             Type[DatabaseFreeListKey],
             Type[DatabaseNameKey],
             Type[EarliestSweepKey],
             Type[EarliestCompactionTimeKey],
             Type[MaxDatabaseIdKey],
             Type[RecoveryBlobJournalKey],
             Type[SchemaVersionKey],
             Type[ScopesPrefixKey]]:
    """Decodes the global metadata key.

    Raises:
      ParserError: if the key contains an unknown metadata key type.
    """
    _, metadata_value = decoder.PeekBytes(1)
    metadata_type = definitions.GlobalMetadataKeyType(metadata_value[0])

    key_class = cls.METADATA_TYPE_TO_CLASS.get(metadata_type)
    if not key_class:
      raise errors.ParserError('Unknown metadata key type')
    return key_class.FromDecoder(
        decoder, key_prefix, base_offset)  #pytype: disable=bad-return-type


@dataclass
class ObjectStoreFreeListKey(BaseIndexedDBKey):
  """An IndexedDB object store free list key.

  Attributes:
    object_store_id: the ID of the object store containing the free list.
  """
  object_store_id: int

  def DecodeValue(self, decoder: utils.LevelDBDecoder):
    """Decodes the object store free list value."""
    raise NotImplementedError('ObjectStoreFreeListKey.decode_value')

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> ObjectStoreFreeListKey:
    """Decodes the object store free list key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.DatabaseMetaDataKeyType.OBJECT_STORE_FREE_LIST:
      raise errors.ParserError('Not am ObjectStoreFreeListKey')
    _, object_store_id = decoder.DecodeVarint()
    return cls(
        offset=base_offset + offset, key_prefix=key_prefix,
        object_store_id=object_store_id)


@dataclass
class IndexFreeListKey(BaseIndexedDBKey):
  """An IndexedDB index free list key.

  Attributes:
    object_store_id: the ID of the object store containing the free list.
  """
  object_store_id: int

  def DecodeValue(self, decoder: utils.LevelDBDecoder):
    """Decodes the index free list value."""
    raise NotImplementedError('IndexFreeListKey.decode_value')

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
    ) -> IndexFreeListKey:
    """Decodes the index free list key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.DatabaseMetaDataKeyType.INDEX_FREE_LIST:
      raise errors.ParserError('Not am IndexFreeListKey')
    _, object_store_id = decoder.DecodeVarint()
    return cls(
        offset=base_offset + offset, key_prefix=key_prefix,
        object_store_id=object_store_id)


@dataclass
class ObjectStoreNamesKey(BaseIndexedDBKey):
  """An IndexedDB object store name key.

  Attributes:
    object_store_name: the name of the object store.
  """
  object_store_name: str

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the object store names value."""
    return decoder.DecodeVarint()[1]

  @classmethod
  def FromDecoder(cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
                 base_offset: int = 0) -> ObjectStoreNamesKey:
    """Decodes the object store names key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.DatabaseMetaDataKeyType.OBJECT_STORE_NAMES:
      raise errors.ParserError('Not am ObjectStoreNamesKey')
    _, object_store_name = decoder.DecodeStringWithLength()
    return cls(key_prefix=key_prefix, offset=base_offset + offset,
               object_store_name=object_store_name)


@dataclass
class IndexNamesKey(BaseIndexedDBKey):
  """An IndexedDB index name key.

  Attributes:
    index_name: the name of the index.
  """
  index_name: str

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the index names value."""
    return decoder.DecodeVarint()[1]

  @classmethod
  def FromDecoder(cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
                 base_offset: int = 0) -> IndexNamesKey:
    """Decodes the index names key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.DatabaseMetaDataKeyType.INDEX_NAMES:
      raise errors.ParserError('Not am IndexNamesKey')
    _, index_name = decoder.DecodeStringWithLength()
    return cls(key_prefix=key_prefix, offset=base_offset + offset,
               index_name=index_name)


@dataclass
class DatabaseMetaDataKey(BaseIndexedDBKey):
  """An IndexedDB database metadata key.

  Attributes:
    metadata_type: the type of metadata that the key value contains.
  """
  metadata_type: definitions.DatabaseMetaDataKeyType

  def DecodeValue(
      self, decoder: utils.LevelDBDecoder) -> Union[str, int]:
    """Decodes the database metadata value."""
    if (self.metadata_type ==
        definitions.DatabaseMetaDataKeyType.ORIGIN_NAME):
      return decoder.DecodeString()[1]
    if (self.metadata_type ==
        definitions.DatabaseMetaDataKeyType.DATABASE_NAME):
      return decoder.DecodeString()[1]
    if (self.metadata_type ==
        definitions.DatabaseMetaDataKeyType.IDB_STRING_VERSION_DATA):
      return decoder.DecodeString()[1]
    if (self.metadata_type ==
        definitions.DatabaseMetaDataKeyType.MAX_ALLOCATED_OBJECT_STORE_ID):
      return decoder.DecodeVarint()[1]
    if (self.metadata_type ==
        definitions.DatabaseMetaDataKeyType.IDB_INTEGER_VERSION):
      return decoder.DecodeVarint()[1]
    if (self.metadata_type ==
        definitions.DatabaseMetaDataKeyType
            .BLOB_NUMBER_GENERATOR_CURRENT_NUMBER):
      return decoder.DecodeVarint()[1]
    raise errors.ParserError(
        f'Unknown database metadata type {self.metadata_type}')

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> Union[
      DatabaseMetaDataKey,
      IndexFreeListKey,
      IndexMetaDataKey,
      IndexNamesKey,
      ObjectStoreFreeListKey,
      ObjectStoreMetaDataKey,
      ObjectStoreNamesKey]:
    """Decodes the database metadata key."""
    offset, metadata_value = decoder.PeekBytes(1)
    metadata_type = definitions.DatabaseMetaDataKeyType(metadata_value[0])

    if metadata_type in (
        definitions.DatabaseMetaDataKeyType.ORIGIN_NAME,
        definitions.DatabaseMetaDataKeyType.DATABASE_NAME,
        definitions.DatabaseMetaDataKeyType.IDB_STRING_VERSION_DATA,
        definitions.DatabaseMetaDataKeyType.MAX_ALLOCATED_OBJECT_STORE_ID,
        definitions.DatabaseMetaDataKeyType.IDB_INTEGER_VERSION,
        definitions.DatabaseMetaDataKeyType
            .BLOB_NUMBER_GENERATOR_CURRENT_NUMBER):
      return cls(key_prefix=key_prefix, offset=base_offset + offset,
                 metadata_type=metadata_type)
    if metadata_type == definitions.DatabaseMetaDataKeyType.INDEX_META_DATA:
      return IndexMetaDataKey.FromDecoder(
          decoder, key_prefix, base_offset)
    if (metadata_type ==
        definitions.DatabaseMetaDataKeyType.OBJECT_STORE_META_DATA):
      return ObjectStoreMetaDataKey.FromDecoder(
          decoder, key_prefix, base_offset)
    if (metadata_type ==
        definitions.DatabaseMetaDataKeyType.OBJECT_STORE_FREE_LIST):
      return ObjectStoreFreeListKey.FromDecoder(
          decoder, key_prefix, base_offset)
    if metadata_type == definitions.DatabaseMetaDataKeyType.INDEX_FREE_LIST:
      return IndexFreeListKey.FromDecoder(
          decoder, key_prefix, base_offset)
    if (metadata_type ==
        definitions.DatabaseMetaDataKeyType.OBJECT_STORE_NAMES):
      return ObjectStoreNamesKey.FromDecoder(
          decoder, key_prefix, base_offset)
    if metadata_type == definitions.DatabaseMetaDataKeyType.INDEX_NAMES:
      return IndexNamesKey.FromDecoder(
          decoder, key_prefix, base_offset)
    raise errors.ParserError(f'unknown database metadata type {metadata_type}.')


@dataclass
class ObjectStoreMetaDataKey(BaseIndexedDBKey):
  """An IndexedDB object store meta data key.

  Attributes:
    object_store_id: the ID of the object store.
    metadata_type: the object store metadata type.
  """
  object_store_id: int
  metadata_type: definitions.ObjectStoreMetaDataKeyType

  def DecodeValue(
      self, decoder: utils.LevelDBDecoder) -> Union[IDBKeyPath, str, bool, int]:
    """Decodes the object store metadata value."""
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.OBJECT_STORE_NAME):
      return decoder.DecodeString()[1]
    if self.metadata_type == definitions.ObjectStoreMetaDataKeyType.KEY_PATH:
      return IDBKeyPath.FromDecoder(decoder)
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.AUTO_INCREMENT_FLAG):
      return decoder.DecodeBool()[1]
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.IS_EVICTABLE):
      return decoder.DecodeBool()[1]
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.LAST_VERSION_NUMBER):
      return decoder.DecodeInt(signed=False)[1]
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.MAXIMUM_ALLOCATED_INDEX_ID):
      return decoder.DecodeInt()[1]
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.HAS_KEY_PATH):
      return decoder.DecodeBool()[1]
    if (self.metadata_type ==
        definitions.ObjectStoreMetaDataKeyType.KEY_GENERATOR_CURRENT_NUMBER):
      return decoder.DecodeInt()[1]
    raise errors.ParserError(f'Unknown metadata type {self.metadata_type}')

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> ObjectStoreMetaDataKey:
    """Decodes the object store metadata key."""
    offset, metadata_value = decoder.DecodeUint8()
    if (metadata_value !=
        definitions.DatabaseMetaDataKeyType.OBJECT_STORE_META_DATA):
      raise errors.ParserError('Not a ObjectStoreMetaDataKey')

    _, object_store_id = decoder.DecodeVarint()
    _, metadata_value = decoder.DecodeUint8()
    metadata_type = definitions.ObjectStoreMetaDataKeyType(metadata_value)
    return cls(
        offset=base_offset + offset, key_prefix=key_prefix,
        object_store_id=object_store_id, metadata_type=metadata_type)

@dataclass
class ObjectStoreDataValue:
  """The parsed values from an ObjectStoreDataKey.

  Attributes:
    unknown: an unknown integer (possibly a sequence number?).
    is_wrapped: True if the value was wrapped.
    blob_size: the blob size, only valid if wrapped.
    blob_offset: the blob offset, only valid if wrapped.
    value: the blink serialized value, only valid if not wrapped.
  """
  unknown: int
  is_wrapped: bool
  blob_size: Optional[int]
  blob_offset: Optional[int]
  value: Any


@dataclass
class ObjectStoreDataKey(BaseIndexedDBKey):
  """An IndexedDB object store data key.

  Attributes:
    encoded_user_key: the encoded user key.
  """
  encoded_user_key: IDBKey

  def DecodeValue(
      self, decoder: utils.LevelDBDecoder) -> ObjectStoreDataValue:
    """Decodes the object store data value."""
    _, unknown_integer = decoder.DecodeVarint()

    _, wrapped_header_bytes = decoder.PeekBytes(3)
    if len(wrapped_header_bytes) != 3:
      raise errors.DecoderError('Insufficient bytes')

    if (wrapped_header_bytes[0] == definitions.BlinkSerializationTag.VERSION and
        wrapped_header_bytes[1] == 0x11 and
        wrapped_header_bytes[2] == 0x01):
      _, blob_size = decoder.DecodeVarint()
      _, blob_offset = decoder.DecodeVarint()
      return ObjectStoreDataValue(
          unknown=unknown_integer,
          is_wrapped=True,
          blob_size=blob_size,
          blob_offset=blob_offset,
          value=None)
    _, blink_bytes = decoder.ReadBytes()
    blink_value = blink.V8ScriptValueDecoder.FromBytes(blink_bytes)
    return ObjectStoreDataValue(
        unknown=unknown_integer,
        is_wrapped=False,
        blob_size=None,
        blob_offset=None,
        value=blink_value)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> ObjectStoreDataKey:
    """Decodes the object store data key."""
    if (key_prefix.GetKeyPrefixType() !=
        definitions.KeyPrefixType.OBJECT_STORE_DATA):
      raise errors.ParserError('Invalid KeyPrefix for ObjectStoreDataKey')
    offset = decoder.stream.tell()
    encoded_user_key = IDBKey.FromDecoder(decoder, offset)
    return cls(
        offset=base_offset + offset,
        key_prefix=key_prefix, encoded_user_key=encoded_user_key)


@dataclass
class ExistsEntryKey(BaseIndexedDBKey):
  """An IndexedDB exists entry key.

  Attributes:
    encoded_user_key: the encoded user key.
  """
  encoded_user_key: IDBKey

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> int:
    """Decodes the exists entry value."""
    _, data = decoder.ReadBytes()
    return int.from_bytes(data, byteorder='little', signed=False)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> ExistsEntryKey:
    """Decodes the exists entry key."""
    offset = decoder.stream.tell()
    encoded_user_key = IDBKey.FromDecoder(decoder, offset)

    return cls(
        offset=base_offset + offset,
        key_prefix=key_prefix, encoded_user_key=encoded_user_key)


@dataclass
class IndexDataKey(BaseIndexedDBKey):
  """An IndexedDB data key.

  Attributes:
    encoded_user_key: the encoded user key.
    sequence_number: the sequence number of the data key.
    encoded_primary_key: the encoded primary key.
  """
  encoded_user_key: IDBKey
  sequence_number: Optional[int]
  encoded_primary_key: Optional[IDBKey]

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> Tuple[int, IDBKey]:
    """Decodes the index data key value."""
    _, version = decoder.DecodeVarint()
    idb_key = IDBKey.FromDecoder(decoder)
    return version, idb_key

  @classmethod
  def FromDecoder(cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
                 base_offset: int = 0) -> IndexDataKey:
    """Decodes the index data key."""
    offset = decoder.stream.tell()
    encoded_user_key = IDBKey.FromDecoder(decoder, offset)

    if decoder.NumRemainingBytes() > 0:
      _, sequence_number = decoder.DecodeVarint()
    else:
      sequence_number = None

    if decoder.NumRemainingBytes() > 0:
      encoded_primary_key_offset = decoder.stream.tell()
      encoded_primary_key = IDBKey.FromDecoder(
          decoder, encoded_primary_key_offset)
    else:
      encoded_primary_key = None

    return cls(
        key_prefix=key_prefix,
        encoded_user_key=encoded_user_key,
        sequence_number=sequence_number,
        encoded_primary_key=encoded_primary_key,
        offset=base_offset + offset)


@dataclass
class BlobEntryKey(BaseIndexedDBKey):
  """An IndexedDB blob entry key.

  Attributes:
    user_key: the user/primary key.
  """
  user_key: IDBKey

  def DecodeValue(
      self, decoder: utils.LevelDBDecoder) -> IndexedDBExternalObject:
    """Decodes the blob entry value."""
    return IndexedDBExternalObject.FromDecoder(decoder)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> BlobEntryKey:
    """Decodes the blob entry key."""
    offset = decoder.stream.tell()
    user_key = IDBKey.FromDecoder(decoder, offset)

    return cls(key_prefix=key_prefix, user_key=user_key,
               offset=base_offset + offset)


@dataclass
class IndexedDbKey(BaseIndexedDBKey):
  """An IndexedDB key.

  A factory class for parsing IndexedDB keys.
  """

  METADATA_TYPE_TO_CLASS = {
      definitions.KeyPrefixType.GLOBAL_METADATA: GlobalMetaDataKey,
      definitions.KeyPrefixType.DATABASE_METADATA: DatabaseMetaDataKey,
      definitions.KeyPrefixType.OBJECT_STORE_DATA: ObjectStoreDataKey,
      definitions.KeyPrefixType.EXISTS_ENTRY: ExistsEntryKey,
      definitions.KeyPrefixType.INDEX_DATA: IndexDataKey,
      definitions.KeyPrefixType.BLOB_ENTRY: BlobEntryKey,
      definitions.KeyPrefixType.INVALID_TYPE: None
  }

  def DecodeValue(self, decoder: utils.LevelDBDecoder) -> Any:
    """Decodes the value from the current position of the LevelDBDecoder.

    Args:
      decoder: the stream decoder
    """

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      key_prefix: KeyPrefix,
      base_offset: int = 0
  ) -> Union[Type[DatabaseMetaDataKey], Type[ExistsEntryKey],
             Type[BlobEntryKey], Type[GlobalMetaDataKey],
             Type[IndexDataKey], Type[ObjectStoreDataKey]]:
    """Decodes the IndexedDB key."""
    key_type = key_prefix.GetKeyPrefixType()
    key_class = cls.METADATA_TYPE_TO_CLASS.get(key_type)
    if not key_class:
      raise errors.ParserError('Unknown KeyPrefixType')
    return key_class.FromDecoder(
        decoder=decoder,
        key_prefix=key_prefix,  #pytype: disable=bad-return-type
        base_offset=base_offset)


@dataclass
class IndexMetaDataKey(BaseIndexedDBKey):
  """An IndexedDB meta data key.

  Attributes:
    object_store_id: the ID of the object store.
    index_id: the index ID.
    metadata_type: the metadata key type.
  """
  object_store_id: int
  index_id: int
  metadata_type: definitions.IndexMetaDataKeyType

  def DecodeValue(
      self, decoder: utils.LevelDBDecoder) -> Union[bool, IDBKeyPath, str]:
    """Decodes the index metadata value."""
    if self.metadata_type == definitions.IndexMetaDataKeyType.INDEX_NAME:
      return decoder.DecodeString()[1]
    if self.metadata_type == definitions.IndexMetaDataKeyType.KEY_PATH:
      return IDBKeyPath.FromDecoder(decoder)
    if (self.metadata_type ==
        definitions.IndexMetaDataKeyType.MULTI_ENTRY_FLAG):
      return decoder.DecodeBool()[1]
    if self.metadata_type == definitions.IndexMetaDataKeyType.UNIQUE_FLAG:
      return decoder.DecodeBool()[1]
    raise errors.ParserError(
        f'Unknown index metadata type {self.metadata_type}')

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      key_prefix: KeyPrefix, base_offset: int = 0
  ) -> IndexMetaDataKey:
    """Decodes the index metadata key."""
    offset, key_type = decoder.DecodeUint8()
    if key_type != definitions.DatabaseMetaDataKeyType.INDEX_META_DATA:
      raise errors.ParserError('Not an IndexMetaDataKey.')
    _, object_store_id = decoder.DecodeVarint()
    _, index_id = decoder.DecodeVarint()
    _, metadata_bytes = decoder.ReadBytes(1)
    metadata_type = definitions.IndexMetaDataKeyType(metadata_bytes[0])
    return cls(offset=base_offset + offset, key_prefix=key_prefix,
               object_store_id=object_store_id, index_id=index_id,
               metadata_type=metadata_type)


@dataclass
class ExternalObjectEntry(utils.FromDecoderMixin):
  """An IndexedDB external object entry.

  Args:
    offset: the offset of the ExternalObjectEntry.
    object_type: the external object type.
    blob_number: the blob number if the object type is a blob or file,
        None otherwise.
    mime_type: the mime type if the object type is a blob or file, None
        otherwise.
    size: the size if the object type is a blob or file, None otherwise.
    filename: the filename if the object is a blob or file, None otherwise.
    last_modified: the last modified time if a blob or file, None otherwise.
    token: the token if a filesystem access handle, None otherwise.
  """
  offset: int = field(compare=False)
  object_type: definitions.ExternalObjectType
  blob_number: Optional[int]
  mime_type: Optional[str]
  size: Optional[int]
  filename: Optional[str]
  last_modified: Optional[int]  # microseconds
  token: Optional[bytes]

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      base_offset: int = 0
  ) -> ExternalObjectEntry:
    """Decodes the external object entry."""
    offset, object_type_value = decoder.DecodeUint8()
    object_type = definitions.ExternalObjectType(object_type_value)
    if (object_type in
        (definitions.ExternalObjectType.BLOB,
         definitions.ExternalObjectType.FILE)):
      _, blob_number = decoder.DecodeVarint()
      _, mime_type = decoder.DecodeStringWithLength()
      _, size = decoder.DecodeVarint()
      if object_type == definitions.ExternalObjectType.FILE:
        _, filename = decoder.DecodeStringWithLength()
        _, last_modified = decoder.DecodeVarint()
      else:
        filename = None
        last_modified = None
      token = None
    else:
      if (object_type ==
          definitions.ExternalObjectType.FILE_SYSTEM_ACCESS_HANDLE):
        _, token = decoder.DecodeBlobWithLength()
      else:
        token = None
      blob_number = None
      mime_type = None
      size = None
      filename = None
      last_modified = None

    return cls(offset=base_offset + offset, object_type=object_type,
        blob_number=blob_number, mime_type=mime_type, size=size,
        filename=filename, last_modified=last_modified, token=token)


@dataclass
class IndexedDBExternalObject(utils.FromDecoderMixin):
  """An IndexedDB external object.

  Args:
    offset: the offset of the IndexedDBExternalObject.
    entries: a list of external objects.
  """
  offset: int = field(compare=False)
  entries: list[ExternalObjectEntry]

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      base_offset: int = 0
  ) -> IndexedDBExternalObject:
    """Decodes the external object."""
    entries = []
    offset = decoder.stream.tell()
    while decoder.NumRemainingBytes():
      entry = ExternalObjectEntry.FromDecoder(decoder, base_offset)
      entries.append(entry)

    return cls(offset=base_offset + offset, entries=entries)


@dataclass
class ObjectStore:
  """An IndexedDB Object Store.

  Attributes:
    id: the object store ID.
    name: the object store name.
    records: the records in the object store.
  """
  id: int
  name: str
  records: list = field(default_factory=list, repr=False)


@dataclass
class IndexedDBRecord:
  """An IndexedDB Record.

  Attributes:
    path: the source file path
    offset: the offset of the record.
    key: the key of the record.
    value: the value of the record.
    sequence_number: if available, the sequence number of the record.
    type: the type of the record.
    level: the leveldb level, if applicable, None can indicate the record
        originated from a log file or the level could not be determined.
    recovered: True if the record is a recovered record.
  """
  path: str
  offset: int
  key: Any
  value: Any
  sequence_number: Optional[int]
  type: int
  level: Optional[int]
  recovered: Optional[bool]

  @classmethod
  def FromLevelDBRecord(
      cls,
      db_record: record.LevelDBRecord
  ) -> IndexedDBRecord:
    """Returns an IndexedDBRecord from a ParsedInternalKey."""
    idb_key = IndexedDbKey.FromBytes(
        db_record.record.key, base_offset=db_record.record.offset)
    idb_value = idb_key.ParseValue(db_record.record.value)
    return cls(
        path=db_record.path,
        offset=db_record.record.offset,
        key=idb_key,
        value=idb_value,
        sequence_number=db_record.record.sequence_number if hasattr(
            db_record.record, 'sequence_number') else None,
        type=db_record.record.record_type,
        level=db_record.level,
        recovered=db_record.recovered)

  @classmethod
  def FromFile(
      cls,
      file_path: pathlib.Path
  ) -> Generator[IndexedDBRecord, None, None]:
    """Yields IndexedDBRecords from a file."""
    for db_record in record.LevelDBRecord.FromFile(file_path):
      try:
        yield cls.FromLevelDBRecord(db_record)
      except(
          errors.ParserError,
          errors.DecoderError,
          NotImplementedError) as err:
        print((
            'Error parsing Indexeddb record: '
            f'{err} at offset {db_record.record.offset} in '
            f'{db_record.path}'),
            file=sys.stderr)
        print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)


class FolderReader:
  """A IndexedDB folder reader for Chrome/Chromium.

  Attributes:
    foldername (str): the source LevelDB folder.
  """

  def __init__(self, foldername: pathlib.Path):
    """Initializes the FileReader.

    Args:
      foldername: the source IndexedDB folder.

    Raises:
      ValueError: if foldername is None or not a directory.
    """
    if not foldername or not foldername.is_dir():
      raise ValueError(f'{foldername} is None or not a directory')
    self.foldername = foldername

  def GetRecords(
      self,
      use_manifest: bool = False
  ) -> Generator[IndexedDBRecord, None, None]:
    """Yield LevelDBRecords.

    Args:
      use_manifest: True to use the current manifest in the folder as a means to
          find the active file set.

    Yields:
      IndexedDBRecord.
    """
    leveldb_folder_reader = record.FolderReader(self.foldername)
    for leveldb_record in leveldb_folder_reader.GetRecords(
        use_manifest=use_manifest):
      try:
        yield IndexedDBRecord.FromLevelDBRecord(
            leveldb_record)
      except(
          errors.ParserError,
          errors.DecoderError,
          NotImplementedError) as err:
        print((
            'Error parsing Indexeddb record: '
            f'{err} at offset {leveldb_record.record.offset} in '
            f'{leveldb_record.path}'),
            file=sys.stderr)
        print(f'Traceback: {traceback.format_exc()}', file=sys.stderr)
