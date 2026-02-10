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
"""Types for indexeddb."""
from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Protocol, Set, runtime_checkable


@dataclasses.dataclass
class JSArray:
  """A parsed Javascript array.

  A JavaScript array behaves like a Python list but allows assigning arbitrary
  properties.  The array is stored in the attribute __array__.

  Attributes:
    values: the array values.
    properties: the array properties.
  """

  values: List[Any] = dataclasses.field(default_factory=list)
  properties: Dict[Any, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class JSSet:
  """A parsed JavaScript set.

  A JavaScript set behaves like a Python set but allows assigning arbitrary
  properties.  The array is stored in the attribute __set__.

  Attributes:
    values: the set values.
    properties: the set properties.
  """

  values: Set[Any] = dataclasses.field(default_factory=set)
  properties: Dict[Any, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Null:
  """A parsed JavaScript Null."""


@dataclasses.dataclass
class RegExp:
  """A parsed JavaScript RegExp.

  Attributes:
    pattern: the pattern.
    flags: the flags.
  """

  pattern: str
  flags: str


@runtime_checkable
class FilterableRecord(Protocol):
  """A protocol for filterable IndexedDB records."""

  @property
  def is_key_filterable(self) -> bool:
    """True if the record key is filterable."""

  @property
  def is_value_filterable(self) -> bool:
    """True if the record value is filterable."""

  @property
  def object_store_id(self) -> int:
    """The object store ID."""

  def MatchesKey(self, term: str) -> bool:
    """Returns True if the record key matches the filter term.

    Args:
      term: the filter term.
    """

  def MatchesValue(self, term: str) -> bool:
    """Returns True if the record value matches the filter term.

    Args:
      term: the filter term.
    """


@dataclasses.dataclass
class Undefined:
  """A JavaScript undef."""
