# dfIndexeddb

dfindexeddb is an experimental Python tool for performing digital forensic
analysis of IndexedDB and LevelDB files.

It parses LevelDB, IndexedDB and JavaScript structures from these files without
requiring native libraries.  (Note: only a subset of IndexedDB key types and
JavaScript types for Chromium-based browsers are currently supported.  Safari
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

Two CLI tools for parsing IndexedDB/LevelDB files are available after
installation:


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

To parse IndexedDB records from a LevelDB folder, use the following command:

```
dfindexeddb db -h
usage: dfindexeddb db [-h] -s SOURCE [--use_manifest] [-o {json,jsonl,repr}]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source leveldb folder
  --use_manifest        Use manifest file to determine active/recovered records.
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
```

To parse IndexedDB records from a LevelDB ldb (.ldb) file, use the following 
command:

```
dfindexeddb ldb -h
usage: dfindexeddb ldb [-h] -s SOURCE [-o {json,jsonl,repr}]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source .ldb file.
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
```

To parse IndexedDB records from a LevelDB log (.log) file, use the following 
command:

```
dfindexeddb log -h
usage: dfindexeddb log [-h] -s SOURCE [-o {json,jsonl,repr}]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source .log file.
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
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

To parse records from a LevelDB folder, use the following command:

```
dfindexeddb db -h
usage: dfindexeddb db [-h] -s SOURCE [--use_manifest] [-o {json,jsonl,repr}]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source leveldb folder
  --use_manifest        Use manifest file to determine active/recovered records.
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
```

To parse records from a LevelDB log (.log) file, use the following command:

```
$ dfleveldb log  -s SOURCE [-o {json,jsonl,repr}] [-t {blocks,physical_records,write_batches,parsed_internal_key}]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source leveldb file
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
  -t {blocks,physical_records,write_batches,parsed_internal_key}, --structure_type {blocks,physical_records,write_batches,parsed_internal_key}
                        Parses the specified structure. Default is parsed_internal_key.
```

To parse records from a LevelDB table (.ldb) file, use the following command:

```
$ dfleveldb ldb -s SOURCE [-o {json,jsonl,repr}] [-t {blocks,records}]

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source leveldb file
  -o {json,jsonl,repr}, --output {json,jsonl,repr}
                        Output format. Default is json
  -t {blocks,records}, --structure_type {blocks,records}
                        Parses the specified structure. Default is records.
```

To parse version edit records from a Descriptor (MANIFEST) file:

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
