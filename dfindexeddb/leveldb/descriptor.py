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
"""Parser for LevelDB Descriptor (MANIFEST) files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator, Optional

from dfindexeddb import errors
from dfindexeddb.leveldb import utils
from dfindexeddb.leveldb import definitions
from dfindexeddb.leveldb import log


@dataclass
class InternalKey:
  """An InternalKey.

  Attributes:
    offset: the offset.
    user_key: the user key.
    sequence_number: the sequence number.
    key_type: the key type.
  """
  offset: int
  user_key: bytes = field(repr=False)
  sequence_number: int
  key_type: int

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0) -> InternalKey:
    """Decodes an InternalKey from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      The InternalKey instance.
    """
    offset, slice_bytes = decoder.DecodeLengthPrefixedSlice()

    if len(slice_bytes) < definitions.PACKED_SEQUENCE_AND_TYPE_LENGTH:
      raise errors.ParserError('Insufficient bytes to parse InternalKey')

    user_key = slice_bytes[:-definitions.SEQUENCE_LENGTH]
    sequence_number = int.from_bytes(
        slice_bytes[-definitions.SEQUENCE_LENGTH:],
        byteorder='little',
        signed=False)
    key_type = slice_bytes[-definitions.PACKED_SEQUENCE_AND_TYPE_LENGTH]

    return cls(
        offset=base_offset + offset,
        user_key=user_key,
        sequence_number=sequence_number,
        key_type=key_type)


@dataclass
class NewFile(utils.FromDecoderMixin):
  """A NewFile.

  Attributes:
    offset: the offset.
    level: the level.
    number: the file number.
    file_size: the file size.
    smallest: the smallest internal key.
    largest: the largest internal key.
  """
  offset: int
  level: int
  number: int
  file_size: int
  smallest: InternalKey
  largest: InternalKey

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0) -> NewFile:
    """Decodes a NewFile from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      The NewFile instance.
    """
    offset, level = decoder.DecodeUint32Varint()
    _, number = decoder.DecodeUint64Varint()
    _, file_size = decoder.DecodeUint64Varint()
    smallest = InternalKey.FromDecoder(decoder, base_offset=base_offset)
    largest = InternalKey.FromDecoder(decoder, base_offset=base_offset)

    return cls(
        offset=offset + base_offset,
        level=level,
        number=number,
        file_size=file_size,
        smallest=smallest,
        largest=largest)


@dataclass
class CompactPointer(utils.FromDecoderMixin):
  """A CompactPointer.

  Attributes:
    offset: the offset.
    level: the level.
    key: the key bytes.
  """
  offset: int
  level: int
  key: bytes = field(repr=False)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0
  ) -> CompactPointer:
    """Decodes a CompactPointer from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      The CompactPointer instance.
    """
    offset, level = decoder.DecodeUint32Varint()
    _, key = decoder.DecodeLengthPrefixedSlice()
    return cls(offset=base_offset + offset, level=level, key=key)


@dataclass
class DeletedFile(utils.FromDecoderMixin):
  """A DeletedFile.

  Attributes:
    offset: the offset.
    level: the level.
    number: the file number.
  """
  offset: int
  level: int
  number: int

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0) -> DeletedFile:
    """Decodes a DeletedFile from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      The DeletedFile instance.
    """
    offset, level = decoder.DecodeUint32Varint()
    _, number = decoder.DecodeUint64Varint()
    return cls(offset=base_offset + offset, level=level, number=number)


@dataclass
class VersionEdit(utils.FromDecoderMixin):
  """A VersionEdit is recorded in a LevelDB descriptor/manifest file.

  Attributes:
    offset: the offset where the VersionEdit was parsed.
    comparator: the comparator.
    log_number: the log number.
    prev_log_number: the previous log number.
    next_file_number: the next file number.
    last_sequence: the last sequence.
    compact_pointers: the list of CompactPointers.
    deleted_files: the list of DeletedFiles.
    new_files: the list of NewFiles.
  """
  offset: int
  comparator: Optional[bytes] = None
  log_number: Optional[int] = None
  prev_log_number: Optional[int] = None
  next_file_number: Optional[int] = None
  last_sequence: Optional[int] = None
  compact_pointers: list[CompactPointer] = field(default_factory=list)
  deleted_files: list[DeletedFile] = field(default_factory=list)
  new_files: list[NewFile] = field(default_factory=list)

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0) -> VersionEdit:
    """Decodes a VersionEdit from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset.

    Returns:
      The VersionEdit instance.

    Raises:
      ParserError if an invalid VersionEditTag is parsed.
    """
    offset, tag_byte = decoder.DecodeUint32Varint()
    version_edit = cls(offset=base_offset + offset)

    while tag_byte:
      try:
        tag = definitions.VersionEditTags(tag_byte)
      except TypeError as error:
        raise errors.ParserError(
            f'Invalid VersionEditTag at offset {offset}') from error

      if tag == definitions.VersionEditTags.COMPARATOR:
        _, version_edit.comparator = decoder.DecodeLengthPrefixedSlice()
      elif tag == definitions.VersionEditTags.LOG_NUMBER:
        _, version_edit.log_number = decoder.DecodeUint64Varint()
      elif tag == definitions.VersionEditTags.PREV_LOG_NUMBER:
        _, version_edit.prev_log_number = decoder.DecodeUint64Varint()
      elif tag == definitions.VersionEditTags.NEXT_FILE_NUMBER:
        _, version_edit.next_file_number = decoder.DecodeUint64Varint()
      elif tag == definitions.VersionEditTags.LAST_SEQUENCE:
        _, version_edit.last_sequence = decoder.DecodeUint64Varint()
      elif tag == definitions.VersionEditTags.COMPACT_POINTER:
        compact_pointer = CompactPointer.FromDecoder(
            decoder=decoder, base_offset=base_offset + offset)
        version_edit.compact_pointers.append(compact_pointer)
      elif tag == definitions.VersionEditTags.DELETED_FILE:
        deleted_file = DeletedFile.FromDecoder(
            decoder=decoder, base_offset=base_offset + offset)
        version_edit.deleted_files.append(deleted_file)
      elif tag == definitions.VersionEditTags.NEW_FILE:
        file_metadata = NewFile.FromDecoder(
            decoder=decoder, base_offset=base_offset + offset)
        version_edit.new_files.append(file_metadata)

      if decoder.NumRemainingBytes() == 0:
        break

      offset, tag_byte = decoder.DecodeUint32Varint()

    return version_edit


class FileReader:
  """A reader for Descriptor files.

  A DescriptorFileReader provides read-only sequential iteration of serialized
  structures in a leveldb Descriptor file.  These structures include:
  * blocks (Block)
  * records (PhysicalRecord)
  * version edits (VersionEdit)
  """
  def __init__(self, filename: str):
    """Initializes the Descriptor a.k.a. MANIFEST file.

    Args:
      filename: the Descriptor filename (e.g. MANIFEST-000001)
    """
    self.filename = filename


  def GetBlocks(self) -> Generator[log.Block, None, None]:
    """Returns an iterator of Block instances.

    A Descriptor file is composed of one or more blocks.

    Yields:
      Block
    """
    with open(self.filename, 'rb') as fh:
      block = log.Block.FromStream(fh)
      while block:
        yield block
        block = log.Block.FromStream(fh)

  def GetPhysicalRecords(self) -> Generator[log.PhysicalRecord, None, None]:
    """Returns an iterator of PhysicalRecord instances.

    A block is composed of one or more physical records.

    Yields:
      PhysicalRecord
    """
    for block in self.GetBlocks():
      yield from block.GetPhysicalRecords()

  def GetVersionEdits(self) -> Generator[VersionEdit, None, None]:
    """Returns an iterator of VersionEdit instances.

    Depending on the VersionEdit size, it can be spread across one or
    more physical records.

    Yields:
      VersionEdit
    """
    buffer = bytearray()
    for physical_record in self.GetPhysicalRecords():
      if (physical_record.record_type ==
          definitions.LogFilePhysicalRecordType.FULL):
        buffer = physical_record.contents
        offset = physical_record.contents_offset + physical_record.base_offset
        version_edit = VersionEdit.FromBytes(buffer, base_offset=offset)
        yield version_edit
        buffer = bytearray()
      elif (physical_record.record_type ==
            definitions.LogFilePhysicalRecordType.FIRST):
        offset = physical_record.contents_offset + physical_record.base_offset
        buffer = bytearray(physical_record.contents)
      elif (physical_record.record_type ==
            definitions.LogFilePhysicalRecordType.MIDDLE):
        buffer.extend(bytearray(physical_record.contents))
      elif (physical_record.record_type ==
            definitions.LogFilePhysicalRecordType.LAST):
        buffer.extend(bytearray(physical_record.contents))
        version_edit = VersionEdit.FromBytes(buffer, base_offset=offset)
        yield version_edit
        buffer = bytearray()
