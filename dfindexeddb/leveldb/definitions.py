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
"""Definitions for LevelDB."""

import enum


PACKED_SEQUENCE_AND_TYPE_LENGTH = 8
SEQUENCE_LENGTH = 7
TYPE_LENGTH = 1


class VersionEditTags(enum.IntEnum):
  """VersionEdit tags."""
  COMPARATOR = 1
  LOG_NUMBER = 2
  NEXT_FILE_NUMBER = 3
  LAST_SEQUENCE = 4
  COMPACT_POINTER = 5
  DELETED_FILE = 6
  NEW_FILE = 7
  # 8 was used for large value refs
  PREV_LOG_NUMBER = 9


class LogFilePhysicalRecordType(enum.IntEnum):
  """Log file physical record types."""
  FULL = 1
  FIRST = 2
  MIDDLE = 3
  LAST = 4
