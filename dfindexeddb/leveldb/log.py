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

import io
import pathlib
from dataclasses import dataclass
from typing import BinaryIO, Generator, Iterable, Optional, Tuple, Union

from dfindexeddb import errors
from dfindexeddb.leveldb import definitions, utils

_CRC32C_POLYNOMIAL = 0x82F63B78
_CRC32C_MASK_DELTA = 0xA282EAD8


def _BuildCrc32cTable() -> Tuple[int, ...]:
  """Builds the 256-entry reflected Castagnoli CRC32C lookup table."""
  table = []
  for index in range(256):
    crc = index
    for _ in range(8):
      if crc & 1:
        crc = (crc >> 1) ^ _CRC32C_POLYNOMIAL
      else:
        crc >>= 1
    table.append(crc & 0xFFFFFFFF)
  return tuple(table)


_CRC32C_TABLE: Tuple[int, ...] = _BuildCrc32cTable()


def ComputeCrc32c(data: bytes, initial_crc: int = 0) -> int:
  """Computes the unmasked Castagnoli CRC32C checksum over bytes.

  Args:
    data: the input byte sequence.
    initial_crc: optional initial CRC32C value for incremental updates.

  Returns:
    The 32-bit unsigned CRC32C value.
  """
  crc = (initial_crc ^ 0xFFFFFFFF) & 0xFFFFFFFF
  for byte_val in data:
    crc = _CRC32C_TABLE[(crc ^ byte_val) & 0xFF] ^ (crc >> 8)
  return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF


def MaskCrc32c(crc: int) -> int:
  """Masks a raw CRC32C checksum per LevelDB's util/crc32c.h specification.

  Args:
    crc: the unmasked 32-bit CRC32C value.

  Returns:
    The masked 32-bit CRC32C value stored in LevelDB headers.
  """
  unsigned_crc = crc & 0xFFFFFFFF
  rotated = (unsigned_crc >> 15) | ((unsigned_crc << 17) & 0xFFFFFFFF)
  return (rotated + _CRC32C_MASK_DELTA) & 0xFFFFFFFF


def UnmaskCrc32c(masked_crc: int) -> int:
  """Unmasks a LevelDB header checksum back to its raw CRC32C value.

  Args:
    masked_crc: the masked 32-bit CRC32C value.

  Returns:
    The unmasked 32-bit CRC32C value.
  """
  rot = (masked_crc - _CRC32C_MASK_DELTA) & 0xFFFFFFFF
  return ((rot >> 17) | ((rot << 15) & 0xFFFFFFFF)) & 0xFFFFFFFF


def ComputeMaskedCrc32c(record_type: int, contents: bytes) -> int:
  """Computes the LevelDB masked CRC32C over record_type || contents.

  Args:
    record_type: the 1-byte physical record type integer.
    contents: the physical record payload bytes.

  Returns:
    The expected 32-bit masked CRC32C value.
  """
  type_crc = ComputeCrc32c(bytes([record_type & 0xFF]))
  return MaskCrc32c(ComputeCrc32c(contents, initial_crc=type_crc))


@dataclass
class ParsedInternalKey:
  """An internal key record from a leveldb log file.

  Attributes:
    offset: the offset of the record.
    record_type: the record type.
    sequence_number: the sequence number (inferred from the relative location
        the ParsedInternalKey in a WriteBatch.)
    key: the record key.
    value: the record value.
  """

  offset: int
  record_type: definitions.InternalRecordType
  sequence_number: int
  key: bytes
  value: bytes

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
    record_type = definitions.InternalRecordType(record_type)

    if record_type == definitions.InternalRecordType.VALUE:
      _, value = decoder.DecodeBlobWithLength()
    elif record_type == definitions.InternalRecordType.DELETED:
      value = b""
    else:
      raise ValueError(f"Invalid record type {record_type}")
    return cls(
        offset=base_offset + offset,
        record_type=record_type,
        key=key,
        value=value,
        sequence_number=sequence_number,
    )


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
  records: Iterable[ParsedInternalKey]

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
          decoder,
          base_offset + offset,
          relative_sequence_number + sequence_number,
      )
      records.append(record)
    return cls(
        offset=base_offset + offset,
        sequence_number=sequence_number,
        count=count,
        records=records,
    )


@dataclass
class PhysicalRecord(utils.FromDecoderMixin):
  """A physical record from a leveldb log file.

  Attributes:
    base_offset: the base offset.
    checksum: the record checksum.
    length: the length of the record in bytes.
    offset: the record offset.
    record_type: the record type.
    contents: the record contents.
    contents_offset: the offset of where the record contents are stored.
    is_valid_checksum: True if checksum matches LevelDB's masked CRC32C.
  """

  base_offset: int
  offset: int
  checksum: int
  length: int
  record_type: definitions.LogFilePhysicalRecordType
  contents: bytes
  contents_offset: int
  is_valid_checksum: bool = True

  PHYSICAL_HEADER_LENGTH = 7

  @classmethod
  def FromDecoder(
      cls,
      decoder: utils.LevelDBDecoder,
      base_offset: int = 0,
      validate_checksum: bool = False,
  ) -> Optional[PhysicalRecord]:
    """Decodes a PhysicalRecord from the current position of a LevelDBDecoder.

    Args:
      decoder: the LevelDBDecoder.
      base_offset: the base offset of the WriteBatch from which the data is
          read from.
      validate_checksum: True to raise ParserError on a CRC32C mismatch.

    Returns:
      A PhysicalRecord or None if the parsed header is 0.

    Raises:
      errors.ParserError: if the record type is invalid or if
          validate_checksum is True and the masked CRC32C check fails.
    """
    offset, checksum = decoder.DecodeUint32()
    _, length = decoder.DecodeUint16()
    _, record_type_byte = decoder.DecodeUint8()
    if checksum == 0 and length == 0 and record_type_byte == 0:
      return None
    if not validate_checksum and (
        checksum == 0 or length == 0 or record_type_byte == 0
    ):
      return None
    try:
      record_type = definitions.LogFilePhysicalRecordType(record_type_byte)
    except ValueError as error:
      raise errors.ParserError(
          f"Error parsing record type of Physical Record at offset "
          f"{offset + base_offset}"
      ) from error
    contents_offset, contents = decoder.ReadBytes(length)
    expected_checksum = ComputeMaskedCrc32c(int(record_type), contents)
    is_valid_checksum = checksum == expected_checksum
    if validate_checksum and not is_valid_checksum:
      raise errors.ParserError(
          f"Checksum mismatch for Physical Record at offset "
          f"{offset + base_offset}: stored=0x{checksum:08x}, "
          f"expected=0x{expected_checksum:08x}"
      )
    return cls(
        base_offset=base_offset,
        offset=offset,
        checksum=checksum,
        length=length,
        record_type=record_type,
        contents=contents,
        contents_offset=contents_offset,
        is_valid_checksum=is_valid_checksum,
    )

  @classmethod
  def FromStream(
      cls,
      stream: BinaryIO,
      base_offset: int = 0,
      validate_checksum: bool = False,
  ) -> Optional[PhysicalRecord]:
    """Decodes a PhysicalRecord from the current position of a binary stream.

    Args:
      stream: the binary stream.
      base_offset: the base offset of the binary stream.
      validate_checksum: True to raise ParserError on a CRC32C mismatch.

    Returns:
      A PhysicalRecord or None if the parsed header is 0.
    """
    decoder = utils.LevelDBDecoder(stream)
    return cls.FromDecoder(
        decoder=decoder,
        base_offset=base_offset,
        validate_checksum=validate_checksum,
    )

  @classmethod
  def FromBytes(
      cls,
      raw_data: Union[bytes, bytearray],
      base_offset: int = 0,
      validate_checksum: bool = False,
  ) -> Optional[PhysicalRecord]:
    """Parses a PhysicalRecord from raw bytes.

    Args:
      raw_data: the raw data.
      base_offset: the base offset of the raw data.
      validate_checksum: True to raise ParserError on a CRC32C mismatch.

    Returns:
      A PhysicalRecord or None if the parsed header is 0.
    """
    stream = io.BytesIO(raw_data)
    return cls.FromStream(
        stream=stream,
        base_offset=base_offset,
        validate_checksum=validate_checksum,
    )


@dataclass
class Block:
  """A block from a leveldb log file.

  Attributes:
    offset: the block offset.
    data: the block data.
  """

  offset: int
  data: bytes

  BLOCK_SIZE = 32768

  def GetPhysicalRecords(
      self, validate_checksum: bool = False
  ) -> Generator[PhysicalRecord, None, None]:
    """Returns a generator of LogFilePhysicalRecords from the block contents.

    Args:
      validate_checksum: True to raise ParserError on a CRC32C mismatch.

    Yields:
      LogFileRecord
    """
    buffer = io.BytesIO(self.data)
    buffer_length = len(self.data)

    while buffer.tell() + PhysicalRecord.PHYSICAL_HEADER_LENGTH < buffer_length:
      record = PhysicalRecord.FromStream(
          buffer,
          base_offset=self.offset,
          validate_checksum=validate_checksum,
      )
      if record:
        yield record
      else:
        return

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
  * physical records (PhysicalRecord)
  * batches (WriteBatch) and
  * key/value records (ParsedInternalKey).

  Attributes:
    filename (str): the leveldb log filename.
    validate_checksum (bool): True to raise ParserError on CRC32C mismatches.
  """

  def __init__(
      self,
      filename: Union[str, pathlib.Path],
      validate_checksum: bool = False,
  ):
    """Initializes the LogFile.

    Args:
      filename: the leveldb log filename.
      validate_checksum: True to raise ParserError on a CRC32C mismatch.
    """
    self.filename = filename
    self.validate_checksum = validate_checksum

  def GetBlocks(self) -> Generator[Block, None, None]:
    """Returns an iterator of Block instances.

    A logfile is composed of one or more blocks.

    Yields:
      a Block
    """
    with open(self.filename, "rb") as fh:
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
      yield from block.GetPhysicalRecords(
          validate_checksum=self.validate_checksum
      )

  def GetWriteBatches(self) -> Generator[WriteBatch, None, None]:
    """Returns an iterator of WriteBatch instances.

    Depending on the batch size, a log file batch can be spread across one or
    more physical records.

    Yields:
      WriteBatch
    """
    buffer = bytearray()
    offset = 0
    for physical_record in self.GetPhysicalRecords():
      if (
          physical_record.record_type
          == definitions.LogFilePhysicalRecordType.FULL
      ):
        offset = physical_record.contents_offset + physical_record.base_offset
        yield WriteBatch.FromBytes(physical_record.contents, base_offset=offset)
        buffer = bytearray()
      elif (
          physical_record.record_type
          == definitions.LogFilePhysicalRecordType.FIRST
      ):
        offset = physical_record.contents_offset + physical_record.base_offset
        buffer = bytearray(physical_record.contents)
      elif (
          physical_record.record_type
          == definitions.LogFilePhysicalRecordType.MIDDLE
      ):
        buffer.extend(bytearray(physical_record.contents))
      elif (
          physical_record.record_type
          == definitions.LogFilePhysicalRecordType.LAST
      ):
        buffer.extend(bytearray(physical_record.contents))
        yield WriteBatch.FromBytes(buffer, base_offset=offset)
        buffer = bytearray()

  def GetParsedInternalKeys(self) -> Generator[ParsedInternalKey, None, None]:
    """Returns an iterator of ParsedInternalKey instances.

    A batch can contain one or more key value records.

    Yields:
      ParsedInternalKey
    """
    for batch in self.GetWriteBatches():
      yield from batch.records
