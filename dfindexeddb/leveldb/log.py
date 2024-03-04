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
"""Parser for LevelDB Log (.log) files."""
from __future__ import annotations

from dataclasses import dataclass, field
import io
from typing import BinaryIO, Generator, Iterable, Optional

from dfindexeddb import utils
from dfindexeddb.leveldb import definitions


@dataclass
class ParsedInternalKey:
  """An internal key record from a leveldb log file.

  Attributes:
    offset: the offset of the record.
    type: the record type.
    sequence_number: the sequence number (inferred from the relative location
        the ParsedInternalKey in a WriteBatch.)
    key: the record key.
    value: the record value.
  """
  offset: int
  type: int
  sequence_number: int
  key: bytes
  value: bytes
  __type__: str = 'ParsedInternalKey'

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      base_offset: int = 0,
      sequence_number: int = 0,
  ) -> ParsedInternalKey:
    """Decodes an internal key value record.

    Args:
      decoder: the leveldb decoder.
      base_offset: the base offset for the parsed internal key value record.
      sequence_number: the sequence number for the parsed internal key value
          record.

    Returns:
      A ParsedInternalKey

    Raises:
      ValueError: if there is an invalid record type encountered.
    """
    offset, record_type = decoder.DecodeUint8()
    _, key = decoder.DecodeBlobWithLength()
    if record_type == 1:
      _, value = decoder.DecodeBlobWithLength()
    elif record_type == 0:
      value =  b''
    else:
      raise ValueError(f'Invalid record type {record_type}')
    return cls(
        offset=base_offset + offset,
        type=record_type,
        key=key,
        value=value,
        sequence_number=sequence_number)


@dataclass
class WriteBatch(utils.FromDecoderMixin):
  """A write batch from a leveldb log file.

  Attributes:
    offset: the write batch offset.
    sequence_number: the batch sequence number.
    count: the number of ParsedInternalKey in the batch.
    records: the ParsedInternalKey parsed from the batch.
  """
  offset: int
  sequence_number: int
  count: int
  records: Iterable[ParsedInternalKey] = field(repr=False)

  @classmethod
  def FromDecoder(
    cls, decoder: utils.LevelDBDecoder, base_offset: int = 0
  ) -> WriteBatch:
    """Parses a WriteBatch from a binary stream.

    Args:
      decoder: the LevelDBDecoder
      base_offset: the base offset of the Block from which the data is
          read from.

    Returns:
      A WriteBatch.
    """
    offset, sequence_number = decoder.DecodeUint64()
    _, count = decoder.DecodeUint32()

    records = []
    for relative_sequence_number in range(count):
      record = ParsedInternalKey.FromDecoder(
          decoder, base_offset + offset,
          relative_sequence_number + sequence_number
      )
      records.append(record)
    return cls(
        offset=base_offset + offset,
        sequence_number=sequence_number,
        count=count,
        records=records)


@dataclass
class PhysicalRecord(utils.FromDecoderMixin):
  """A physical record from a leveldb log file.

  Attributes:
    offset: the record offset.
    checksum: the record checksum.
    length: the length of the record in bytes.
    type: the record type.
    contents: the record contents.
    contents_offset: the offset of where the record contents are stored.
  """
  base_offset: int
  offset: int
  checksum: int
  length: int
  record_type: definitions.LogFilePhysicalRecordType
  contents: bytes = field(repr=False)
  contents_offset: int

  PHYSICAL_HEADER_LENGTH = 7

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, base_offset: int = 0
  ) -> PhysicalRecord:
    """Decodes a PhysicalRecord from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset of the WriteBatch from which the data is
          read from.

    Returns:
      A PhysicalRecord.
    """
    offset, checksum = decoder.DecodeUint32()
    _, length = decoder.DecodeUint16()
    record_type = definitions.LogFilePhysicalRecordType(
        decoder.DecodeUint8()[1])
    contents_offset, contents = decoder.ReadBytes(length)
    return cls(
        base_offset=base_offset,
        offset=offset,
        checksum=checksum,
        length=length,
        record_type=record_type,
        contents=contents,
        contents_offset=contents_offset)


@dataclass
class Block:
  """A block from a leveldb log file.

  Attributes:
    offset: the block offset.
    data: the block data.
  """
  offset: int
  data: bytes = field(repr=False)

  BLOCK_SIZE = 32768

  def GetPhysicalRecords(self) -> Generator[PhysicalRecord, None, None]:
    """Returns a generator of LogFilePhysicalRecords from the block contents.

    Yields:
      LogFileRecord
    """
    buffer = io.BytesIO(self.data)
    buffer_length = len(self.data)

    while buffer.tell() + PhysicalRecord.PHYSICAL_HEADER_LENGTH < buffer_length:
      yield PhysicalRecord.FromStream(buffer, base_offset=self.offset)

  @classmethod
  def FromStream(cls, stream: BinaryIO) -> Optional[Block]:
    """Parses a Block from a binary stream.

    Args:
      stream: the binary stream to be parsed.

    Returns:
      the Block or None if there is no data to read from the stream.
    """
    offset = stream.tell()
    data = stream.read(cls.BLOCK_SIZE)  # reads full and partial blocks
    if not data:
      return None
    return cls(offset, data)


class FileReader:
  """A leveldb log file reader.

  A Log FileReader provides read-only sequential iteration of serialized
  structures in a leveldb logfile.  These structures include:
  * blocks (Block)
  * phyiscal records (PhysicalRecord)
  * batches (WriteBatch) and
  * key/value records (ParsedInternalKey).

  Attributes:
    filename (str): the leveldb log filename.
  """

  def __init__(self, filename: str):
    """Initializes the LogFile.

    Args:
      filename: the leveldb log filename
    """
    self.filename = filename

  def GetBlocks(self) -> Generator[Block, None, None]:
    """Returns an iterator of Block instances.

    A logfile is composed of one or more blocks.

    Yields:
      a Block
    """
    with open(self.filename, 'rb') as fh:
      block = Block.FromStream(fh)
      while block:
        yield block
        block = Block.FromStream(fh)

  def GetPhysicalRecords(self) -> Generator[PhysicalRecord, None, None]:
    """Returns an iterator of PhysicalRecord instances.

    A block is composed of one or more physical records.

    Yields:
      PhysicalRecord
    """
    for block in self.GetBlocks():
      yield from block.GetPhysicalRecords()

  def GetWriteBatches(self) -> Generator[WriteBatch, None, None]:
    """Returns an iterator of WriteBatch instances.

    Depending on the batch size, a log file batch can be spread across one or
    more physical records.

    Yields:
      WriteBatch
    """
    buffer = bytearray()
    for physical_record in self.GetPhysicalRecords():
      if(physical_record.record_type ==
         definitions.LogFilePhysicalRecordType.FULL):
        buffer = physical_record.contents
        offset = physical_record.contents_offset + physical_record.base_offset
        yield WriteBatch.FromBytes(buffer, base_offset=offset)
        buffer = bytearray()
      elif (physical_record.record_type
            == definitions.LogFilePhysicalRecordType.FIRST):
        offset = physical_record.contents_offset + physical_record.base_offset
        buffer = bytearray(physical_record.contents)
      elif (physical_record.record_type ==
            definitions.LogFilePhysicalRecordType.MIDDLE):
        buffer.extend(bytearray(physical_record.contents))
      elif (physical_record.record_type ==
            definitions.LogFilePhysicalRecordType.LAST):
        buffer.extend(bytearray(physical_record.contents))
        yield WriteBatch.FromBytes(buffer, base_offset=offset)
        buffer = bytearray()

  def GetKeyValueRecords(self) -> Generator[ParsedInternalKey, None, None]:
    """Returns an iterator of KeyValueRecord instances.

    A batch can contain on or more key value records.

    Yields:
      KeyValueRecord
    """
    for batch in self.GetWriteBatches():
      yield from batch.records
