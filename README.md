# dfIndexeddb

dfindexeddb is an experimental Python tool for performing digital forensic
analysis of IndexedDB and leveldb files.

It parses leveldb, IndexedDB and javascript structures from these files without
requiring native libraries.

The content of IndexedDB files is dependent on what a web application stores
locally/offline using the web browser's
[IndexedDB API](https://www.w3.org/TR/IndexedDB/).  Examples of content might
include:
* text from a text/source-code editor application,
* emails and contact information from an e-mail application,
* images and metadata from a photo gallery application

## Installation from source

### Linux

1. Install the snappy compression development package

```
    $ sudo apt install libsnappy-dev
```

2. Clone or download the repository to your local machine.

3. Create a virutal environemnt and install the package

```
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ pip install .
```

## Tools

This repository contains a number of scripts which demonstrate how one can use
this library.  To run these tools, please install the `click` python package.

* `tools/indexeddb_dump.py` - parses structures from an IndexedDB and prints
them to standard output.
  - Optionally, you can also install the `leveldb` python package if you
  would prefer to use a native leveldb library instead of the leveldb parser in
  this repository.
* `tools/ldb_dump.py` - parses structures from a LevelDB .ldb file and prints
them to standard output.
* `tools/log_dump.py` - parses structures from a LevelDB .log file and prints
them to standard output.



```
    $ pip install click leveldb
```
