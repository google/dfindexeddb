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

## Installation

```
$ pip install dfindexeddb
```

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

## Usage

A CLI tool is available after installation:

```
$ dfindexeddb -h
usage: dfindexeddb [-h] -s SOURCE [--json] {log,ldb,indexeddb} ...

A cli tool for the dfindexeddb package

positional arguments:
  {log,ldb,indexeddb}

options:
  -s SOURCE, --source SOURCE
                        The source leveldb file
  --json                Output as JSON
```

To parse a LevelDB .log file:

```
$ dfindexeddb -s <SOURCE> log -h
usage: dfindexeddb log [-h] {blocks,physical_records,write_batches,parsed_internal_key,records}

positional arguments:
  {blocks,physical_records,write_batches,parsed_internal_key,records}

options:
  -h, --help            show this help message and exit
```

To parse a LevelDB .ldb file:

```
$ dfindexeddb -s <SOURCE> ldb -h
usage: dfindexeddb ldb [-h] {blocks,records}

positional arguments:
  {blocks,records}

options:
  -h, --help        show this help message and exit
```

To parse a LevelDB .ldb or .log file as IndexedDB:

```
$ dfindexeddb -s <SOURCE> indexeddb -h
usage: dfindexeddb indexeddb [-h]

options:
  -h, --help  show this help message and exit
```
