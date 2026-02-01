"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import leveldb


def generate_test_data_put():
  db = leveldb.LevelDB("create key", error_if_exists=True)
  db.Put(key=b"test str", value=b"test value")
  return db


def generate_test_data_delete():
  db = leveldb.LevelDB("delete key", error_if_exists=True)
  db.Put(key=b"test str", value=b"test value")
  db.Delete(key=b"test str")


def generate_test_logfilerecord():
  db = leveldb.LevelDB("large logfilerecord", error_if_exists=True)
  db.Put(key=b"A", value=b"0" * 1000)
  db.Put(key=b"B", value=b"1" * 97270)
  db.Put(key=b"C", value=b"2" * 8000)


def generate_test_data_put_large():
  db = leveldb.LevelDB("create large key", error_if_exists=True)
  db.Put(key=b"AAAAAAAA" * 1024 * 1024, value=b"test value")
  db.Put(key=b"BBBBBBBB", value=b"CCCCCCCC" * 1024 * 1024)


def generate_test_data_delete_large():
  db = leveldb.LevelDB("delete large key", error_if_exists=True)
  db.Put(key=b"AAAAAAAA" * 1024 * 1024, value=b"test value")
  db.Put(key=b"BBBBBBBB", value=b"CCCCCCCC" * 1024 * 1024)
  db.Delete(key=b"AAAAAAAA" * 1024 * 1024)


def generate_test_data_100000_keys():
  db = leveldb.LevelDB("100k keys", error_if_exists=True)
  for i in range(100000):
    i_bytes = i.to_bytes(byteorder="little", length=4)
    db.Put(key=i_bytes, value=b"test value" + i_bytes)


def generate_test_data_100000_keys_delete():
  db = leveldb.LevelDB("100k keys delete", error_if_exists=True)
  for i in range(100000):
    i_bytes = i.to_bytes(byteorder="little", length=4)
    db.Put(key=i_bytes, value=b"test value" + i_bytes)

  for i in range(0, 10000, 1000):
    i_bytes = i.to_bytes(byteorder="little", length=4)
    db.Delete(i_bytes)


if __name__ == "__main__":
  generate_test_data_put()
  generate_test_data_delete()
  generate_test_logfilerecord()
  generate_test_data_put_large()
  generate_test_data_delete_large()
  generate_test_data_100000_keys()
  generate_test_data_100000_keys_delete()
