# dfIndexeddb

dfindexeddb is an experimental Python tool for performing digital forensic
analysis of IndexedDB and LevelDB files.

It parses LevelDB, IndexedDB and JavaScript structures from these files without
requiring native libraries.  (Note: only a subset of IndexedDB key types and
JavaScript types for Safari and Chromium-based browsers are currently supported.
Firefox is under development).

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

Two CLI tools for parsing IndexedDB/LevelDB files are available after installation:


### IndexedDB

```
$ dfindexeddb -h
usage: dfindexeddb [-h] {db,ldb,log} ...

A cli tool for parsing indexeddb files

positional arguments:
  {db,ldb,log}
    db          Parse a directory as indexeddb.
    ldb         Parse a ldb file as indexeddb.
    log         Parse a log file as indexeddb.

options:
  -h, --help    show this help message and exit
```

#### Examples:

To parse IndexedDB records from an sqlite file for Safari and output the results as JSON-L, use the following command:

```
dfindexeddb db -s SOURCE --format safari -o jsonl
```

To parse IndexedDB records from a LevelDB folder for Chrome/Chromium, using the manifest file to determine recovered records and output as JSON, use the following command:

```
dfindexeddb db -s SOURCE --format chrome --use_manifest
```

To parse IndexedDB records from a LevelDB ldb (.ldb) file and output the results as JSON-L, use the following command:

```
dfindexeddb ldb -s SOURCE -o jsonl
```

To parse IndexedDB records from a LevelDB log (.log) file and output the results as the Python printable representation, use the following command:

```
dfindexeddb log -s SOURCE -o repr
```

To parse a file as a Chrome/Chromium IndexedDB blink value and output the results as JSON:

```
dfindexeddb blink -s SOURCE
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

#### Examples

To parse records from a LevelDB folder, use the following command:

```
dfindexeddb db -s SOURCE
```

To parse blocks / physical records/ write batches / internal key records from a LevelDB log (.log) file, use the following command, specifying the type (block, physical_records, etc) via the `-t` option.  By default, internal key records are parsed:

```
$ dfleveldb log  -s SOURCE [-t {blocks,physical_records,write_batches,parsed_internal_key}]
```

To parse blocks / records from a LevelDB table (.ldb) file, use the following command, specifying the type (blocks, records) via the `-t` option.  By default, records are parsed:

```
$ dfleveldb ldb -s SOURCE [-t {blocks,records}]
```

To parse version edit records from a Descriptor (MANIFEST) file, use the following command:

```
$ dfleveldb descriptor -s SOURCE [-o {json,jsonl,repr}] [-t {blocks,physical_records,versionedit} | -v]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source leveldb file
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
  -t {blocks,physical_records,versionedit}, --structure_type {blocks,physical_records,versionedit}
                        Parses the specified structure. Default is versionedit.
  -v, --version_history
                        Parses the leveldb version history.
```
