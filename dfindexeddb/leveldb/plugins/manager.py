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
"""Leveldb plugin manager."""
from typing import Iterable, Type

from dfindexeddb.leveldb.plugins import interface


class LeveldbPluginManager:
  """The leveldb plugin manager."""

  _class_registry: dict[str, Type[interface.LeveldbPlugin]] = {}

  @classmethod
  def GetPlugins(cls) -> Iterable[tuple[str, type[interface.LeveldbPlugin]]]:
    """Retrieves the registered leveldb plugins.

    Yields:
      tuple: containing:
        str: the name of the leveldb plugin.
        class: the plugin class.
    """
    yield from cls._class_registry.items()

  @classmethod
  def GetPlugin(cls, plugin_name: str) -> type[interface.LeveldbPlugin]:
    """Retrieves a class object of a specific plugin.

    Args:
      plugin_name: name of the plugin.

    Returns:
      the LeveldbPlugin class.

    Raises:
      KeyError: if the plugin is not found/registered in the manager.
    """
    try:
      return cls._class_registry[plugin_name]
    except KeyError as exc:
      raise KeyError(f"Plugin not found: {plugin_name}") from exc

  @classmethod
  def RegisterPlugin(cls, plugin_class: Type[interface.LeveldbPlugin]) -> None:
    """Registers a leveldb plugin.

    Args:
      plugin_class (class): the plugin class to register.

    Raises:
      KeyError: if class is already set for the corresponding name.
    """
    plugin_name = plugin_class.__name__
    if plugin_name in cls._class_registry:
      raise KeyError(f"Plugin already registered {plugin_name}")
    cls._class_registry[plugin_name] = plugin_class

  @classmethod
  def ClearPlugins(cls) -> None:
    """Clears all plugin registrations."""
    cls._class_registry = {}


PluginManager = LeveldbPluginManager()  # pylint: disable=invalid-name
