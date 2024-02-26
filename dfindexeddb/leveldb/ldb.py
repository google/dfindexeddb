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
"""Parser for LevelDB Table (.ldb) files."""
from __future__ import annotations

from dataclasses import dataclass, field
import io
import os
from typing import BinaryIO, Iterable, Tuple

import snappy
import zstd

from dfindexeddb import utils


@dataclass
class LdbKeyValueRecord:
  """A leveldb table key-value record.

  Attributes:
    offset: the offset of the record.
    key: the key of the record.
    value: the value of the record.
    sequence_number: the sequence number of the record.
    type: the type of the record.
  """
  offset: int
  key: bytes
  value: bytes
  sequence_number: int
  type: int

  PACKED_SEQUENCE_AND_TYPE_LENGTH = 8
  SEQUENCE_LENGTH = 7
  TYPE_LENGTH = 1

  @classmethod
  def FromDecoder(
      cls, decoder: utils.LevelDBDecoder, block_offset: int, shared_key: bytes
  ) -> Tuple[LdbKeyValueRecord, bytes]:
    """Decodes a ldb key value record.

    Args:
      decoder: the leveldb decoder.
      block_offset: the block offset.
      shared_key: the shared key bytes.

    Returns:
      A tuple of the parsed LdbKeyValueRecord and the updated shared key bytes.
    """
    offset, shared_bytes = decoder.DecodeUint32Varint()
    _, unshared_bytes = decoder.DecodeUint32Varint()
    _, value_length = decoder.DecodeUint32Varint()
    _, key_delta = decoder.ReadBytes(unshared_bytes)
    _, value = decoder.ReadBytes(value_length)

    shared_key = shared_key[:shared_bytes] + key_delta
    key = shared_key[:-cls.PACKED_SEQUENCE_AND_TYPE_LENGTH]
    sequence_number = int.from_bytes(
        key[-cls.SEQUENCE_LENGTH:], byteorder='little', signed=False)
    key_type = shared_key[-cls.PACKED_SEQUENCE_AND_TYPE_LENGTH]

    return cls(offset + block_offset, key, value, sequence_number,
               key_type), shared_key


@dataclass
class LdbBlock:
  """A leveldb table block.

  Attributes:
    offset: the offset of the block.
    block_offset:
  """
  offset: int
  block_offset: int
  length: int
  data: bytes = field(repr=False)
  footer: bytes  # 5 bytes = 1 byte compressed flag + 4 bytes checksum.

  SNAPPY_COMPRESSED = 1
  ZSTD_COMPRESSED = 2
  RESTART_ENTRY_LENGTH = 4

  def IsSnappyCompressed(self) -> bool:
    """Returns true if the block is snappy compressed."""
    return self.footer[0] == self.SNAPPY_COMPRESSED

  def IsZstdCompressed(self) -> bool:
    """Returns true if the block is zstd compressed."""
    return self.footer[0] == self.ZSTD_COMPRESSED

  def GetBuffer(self) -> bytes:
    """Returns the block buffer, decompressing if required."""
    if self.IsSnappyCompressed():
      return snappy.decompress(self.data)
    if self.IsZstdCompressed():
      return zstd.decompress(self.data)
    return self.data

  def GetRecords(self) -> Iterable[LdbKeyValueRecord]:
    """Returns an iterator over the key value records in the block.

    Yields:
      LdbKeyValueRecords
    """
    # get underlying block content, decompressing if required
    buffer = self.GetBuffer()
    decoder = utils.LevelDBDecoder(io.BytesIO(buffer))

    # trailer of a block has the form:
    #    restarts: uint32[num_restarts]
    #    num_restarts: uint32
    decoder.stream.seek(-self.RESTART_ENTRY_LENGTH, os.SEEK_END)
    _, num_restarts = decoder.DecodeUint32()
    restarts_offset = (
        decoder.stream.tell()) - (num_restarts + 1) * self.RESTART_ENTRY_LENGTH

    decoder.stream.seek(restarts_offset)
    _, offset = decoder.DecodeUint32()
    decoder.stream.seek(offset)
    key = b''

    while decoder.stream.tell() < restarts_offset:
      key_value_record, key = LdbKeyValueRecord.FromDecoder(
          decoder, self.block_offset, key)
      yield key_value_record

    # TODO: parse trailer of the block for restart points (where the full
    # key is stored to allow for binary lookup).  It's not needed at this time
    # since we are sequentially iterating over the records in the block/file.


@dataclass
class BlockHandle:
  """A handle to a block in the ldb file.

  Attributes:
    offset: the offset of the block handle.
    block_offset: the offset of the block.
    length: the length of the block.
  """
  offset: int
  block_offset: int
  length: int

  BLOCK_TRAILER_SIZE = 5

  def Load(self, stream: BinaryIO) -> LdbBlock:
    """Loads the block data.

    Args:
      stream: the binary stream of the ldb file.

    Returns:
      a LdbBlock.

    Raises:
      ValueError: if it could not read all of the block or block footer.
    """
    stream.seek(self.block_offset, os.SEEK_SET)
    data = stream.read(self.length)
    if len(data) != self.length:
      raise ValueError('Could not read all of the block')

    footer = stream.read(self.BLOCK_TRAILER_SIZE)
    if len(footer) != self.BLOCK_TRAILER_SIZE:
      raise ValueError('Could not read all of the block footer')

    return LdbBlock(self.offset, self.block_offset, self.length, data, footer)

  @classmethod
  def FromStream(cls, stream: BinaryIO, base_offset: int = 0) -> BlockHandle:
    """Reads a block handle from a binary stream.

    Args:
      stream: the binary stream.
      base_offset: the base offset.

    Returns:
      A BlockHandle.
    """
    decoder = utils.LevelDBDecoder(stream)
    offset, block_offset = decoder.DecodeUint64Varint()
    _, length = decoder.DecodeUint64Varint()
    return cls(offset + base_offset, block_offset, length)


class LdbFileReader:
  """A leveldb table (.ldb or .sst) file reader.

  A LdbFileReader provides read-only sequential iteration of serialized
  structures in a leveldb ldb file.  These structures include:
  * blocks (LdbBlock)
  * records (LdbKeyValueRecord)
  """

  FOOTER_SIZE = 48
  MAGIC = b'\x57\xfb\x80\x8b\x24\x75\x47\xdb'

  def __init__(self, filename: str):
    """Initializes the LogFile.

    Args:
      filename: the .ldb filename.

    Raises:
      ValueError if the file has an invalid magic number at the end.
    """
    self.filename = filename
    with open(self.filename, 'rb') as fh:
      fh.seek(-len(self.MAGIC), os.SEEK_END)
      if fh.read(len(self.MAGIC)) != self.MAGIC:
        raise ValueError(f'Invalid magic number in {self.filename}')

      fh.seek(-self.FOOTER_SIZE, os.SEEK_END)
      # meta_handle, need to read first due to variable integers
      _ = BlockHandle.FromStream(fh)
      index_handle = BlockHandle.FromStream(fh)

      # self.meta_block = meta_handle.load(fh)  # TODO: support meta blocks
      self.index_block = index_handle.Load(fh)

  def GetBlocks(self) -> Iterable[LdbBlock]:
    """Returns an iterator of LdbBlocks.

    Yields:
      LdbBlock.
    """
    with open(self.filename, 'rb') as fh:
      for key_value_record in self.index_block.GetRecords():
        block_handle = BlockHandle.FromStream(
            io.BytesIO(key_value_record.value),
            base_offset=key_value_record.offset)
        yield block_handle.Load(fh)

  def GetKeyValueRecords(self) -> Iterable[LdbKeyValueRecord]:
    """Returns an iterator of LdbKeyValueRecords.

    Yields:
      LdbKeyValueRecords.
    """
    for block in self.GetBlocks():
      yield from block.GetRecords()

  def RangeIter(self) -> Iterable[Tuple[bytes, bytes]]:  #pylint: disable=C0103
    """Returns an iterator of key-value pairs.

    Yields:
      A tuple of key and value as bytes.
    """
    for record in self.GetKeyValueRecords():
      yield (record.key, record.value)
