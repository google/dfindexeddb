# dfIndexeddb

dfindexeddb is an experimental Python tool for performing digital forensic
analysis of IndexedDB and leveldb files.

It parses leveldb, IndexedDB and javascript structures from these files without
requiring native libraries.  (Note: only a subset of IndexedDB key types and
Javascript types for Chromium-based browsers are currently supported.  Safari
and Firefox are under development).

The content of IndexedDB files is dependent on what a web application stores
locally/offline using the web browser's
[IndexedDB API](https://www.w3.org/TR/IndexedDB/).  Examples of content might
include:
* text from a text/source-code editor application,
* emails and contact information from an e-mail application,
* images and metadata from a photo gallery application


## Installation

1. [Linux] Install the snappy compression development package

```
    $ sudo apt install libsnappy-dev
```

2. Create a virtual environment and install the package

```
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ pip install dfindexeddb
```

## Installation from source

1. [Linux] Install the snappy compression development package

```
    $ sudo apt install libsnappy-dev
```

2. Clone or download/unzip the repository to your local machine.

3. Create a virtual environment and install the package

```
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ pip install .
```

## Usage

Two CLI tools for parsing IndexedDB/leveldb files are available after
installation:


### IndexedDB

```
$ dfindexeddb -h
usage: dfindexeddb [-h] -s SOURCE [--json]

A cli tool for parsing indexeddb files

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source leveldb folder
  --json                Output as JSON
```

### LevelDB

```
$ dfleveldb -h
usage: dfleveldb [-h] {db,log,ldb,descriptor} ...

A cli tool for parsing leveldb files

positional arguments:
  {db,log,ldb,descriptor}
    db                  Parse a directory as leveldb.
    log                 Parse a leveldb log file.
    ldb                 Parse a leveldb table (.ldb) file.
    descriptor          Parse a leveldb descriptor (MANIFEST) file.

options:
  -h, --help            show this help message and exit
```

To parse records from a LevelDB log (.log) file, use the following command:

```
$ dfleveldb log -s <SOURCE> [--json]
```

To parse records from a LevelDB table (.ldb) file, use the following command:

```
$ dfleveldb ldb -s <SOURCE> [--json]
```

To parse version edit records from a Descriptor (MANIFEST) file:

```
$ dfleveldb descriptor -s <SOURCE> [--json]
```
