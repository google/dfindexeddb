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
from enum import IntEnum
import io
from typing import BinaryIO, Generator, Iterable, Optional

from dfindexeddb import utils


class LogFilePhysicalRecordType(IntEnum):
  """LevelDB log file physical record types."""
  FULL = 1
  FIRST = 2
  MIDDLE = 3
  LAST = 4


@dataclass
class ParsedInternalKey:
  """An internal key record from a leveldb log file.

  Attributes:
    offset: the offset of the record.
    type: the record type.
    key: the record key.
    value: the record value.
  """
  offset: int
  type: int
  key: bytes
  value: bytes

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      base_offset: int = 0
  ) -> ParsedInternalKey:
    """Decodes an internal key value record.

    Args:
      decoder: the leveldb decoder.
      base_offset: the base offset for the parsed key value record.

    Returns:
      a ParsedInternalKey

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
    return cls(base_offset + offset, record_type, key, value)


@dataclass
class WriteBatch:
  """A write batch from a leveldb log file.

  Attributes:
    offset: the batch offset.
    sequence_number: the batch sequence number.
    count: the number of ParsedInternalKey in the batch.
    records: the ParsedInternalKey parsed from the batch.
  """
  offset: int
  sequence_number: int
  count: int
  records: Iterable[ParsedInternalKey] = field(repr=False)

  @classmethod
  def FromStream(
    cls, stream: BinaryIO, base_offset: int = 0
  ) -> WriteBatch:
    """Parses a WriteBatch from a binary stream.

    Args:
      stream: the binary stream to be parsed.
      base_offset: the base offset of the Block from which the data is
          read from.

    Returns:
      A WriteBatch.
    """
    decoder = utils.LevelDBDecoder(stream)
    _, sequence_number = decoder.DecodeUint64()
    _, count = decoder.DecodeUint32()

    records = []
    for _ in range(count):
      record = ParsedInternalKey.FromDecoder(decoder, base_offset)
      records.append(record)
    return cls(base_offset, sequence_number, count, records)

  @classmethod
  def FromBytes(cls, data: bytes, base_offset: int = 0) -> WriteBatch:
    """Parses a WriteBatch from bytes.

    Args:
      data: the bytes to be parsed.
      base_offset: the base offset of the Block from which the data is
          read from.

    Returns:
      A WriteBatch.
    """
    return cls.FromStream(io.BytesIO(data), base_offset)


@dataclass
class PhysicalRecord:
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
  record_type: LogFilePhysicalRecordType
  contents: bytes = field(repr=False)
  contents_offset: int

  @classmethod
  def FromStream(
      cls, stream: BinaryIO, base_offset: int = 0) -> PhysicalRecord:
    """Parses a PhysicalRecord from a binary stream.

    Args:
      stream: the binary stream to be parsed.
      base_offset: the base offset of the WriteBatch from which the data is
          read from.

    Returns:
      A PhysicalRecord.
    """
    decoder = utils.StreamDecoder(stream)
    offset, checksum = decoder.DecodeUint32()
    _, length = decoder.DecodeUint16()
    record_type = LogFilePhysicalRecordType(decoder.DecodeUint8()[1])
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

    while buffer.tell() < buffer_length:
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


class LogFileReader:
  """A leveldb log file reader.

  A LogFileReader provides read-only sequential iteration of serialized
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
      while True:
        block = Block.FromStream(fh)
        if not block:
          break
        yield block

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
      if physical_record.record_type == LogFilePhysicalRecordType.FULL:
        buffer = physical_record.contents
        offset = physical_record.contents_offset + physical_record.base_offset
        yield WriteBatch.FromBytes(buffer, base_offset=offset)
        buffer = bytearray()
      elif physical_record.record_type == LogFilePhysicalRecordType.FIRST:
        offset = physical_record.contents_offset + physical_record.base_offset
        buffer = bytearray(physical_record.contents)
      elif physical_record.record_type == LogFilePhysicalRecordType.MIDDLE:
        buffer.extend(bytearray(physical_record.contents))
      elif physical_record.record_type == LogFilePhysicalRecordType.LAST:
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
