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
"""Interface for leveldb plugins."""
from typing import Union

from dfindexeddb.leveldb import record


class LeveldbPlugin:

  @classmethod
  def FromLevelDBRecord(cls,
      ldb_record: record.LevelDBRecord):
    """Parses a leveldb record."""
    parsed_record = cls.FromKeyValueRecord(ldb_record.record)
    ldb_record.record = parsed_record
    return ldb_record

  @classmethod
  def FromKeyValueRecord(cls, ldb_record):
    """Parses a leveldb key value record."""
