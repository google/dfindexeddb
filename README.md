# dfIndexeddb

dfindexeddb is an experimental Python tool for performing digital forensic
analysis of IndexedDB and LevelDB files.

It parses LevelDB, IndexedDB and JavaScript structures from these files without
requiring native libraries.  (Note: only a subset of IndexedDB key types and
JavaScript types for Firefox, Safari and Chromium-based browsers are currently supported).

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

### Optional plugins

To also install the dependencies for leveldb/indexeddb plugins, run
```
    $ pip install 'dfindexeddb[plugins]'
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

### Optional plugins

To also install the dependencies for leveldb/indexeddb plugins, run
```
    $ pip install '.[plugins]'
```

## Usage

Two CLI tools for parsing IndexedDB/LevelDB files are available after
installation:


### IndexedDB

```
$ dfindexeddb -h
usage: dfindexeddb [-h] {blink,gecko,db,ldb,log} ...

A cli tool for parsing IndexedDB files

positional arguments:
  {blink,gecko,db,ldb,log}
    blink               Parse a file as a blink-encoded value.
    gecko               Parse a file as a gecko-encoded value.
    db                  Parse a directory/file as IndexedDB.
    ldb                 Parse a ldb file as IndexedDB.
    log                 Parse a log file as IndexedDB.

options:
  -h, --help    show this help message and exit
```

#### Examples:

| Platform / Source | Format | Command |
| :--- | :--- | :--- |
| **Firefox** (sqlite) | JSON | `dfindexeddb db -s SOURCE --format firefox -o json` |
| **Safari** (sqlite) | JSON-L | `dfindexeddb db -s SOURCE --format safari -o jsonl` |
| **Chrome** (LevelDB/sqlite) | JSON | `dfindexeddb db -s SOURCE --format chrome` |
| **Chrome** (.ldb) | JSON-L | `dfindexeddb ldb -s SOURCE -o jsonl` |
| **Chrome** (.log) | Python repr | `dfindexeddb log -s SOURCE -o repr` |
| **Chrome** (Blink) | JSON | `dfindexeddb blink -s SOURCE` |
| **Filter Records by key** | JSON | `dfindexeddb db -s SOURCE --format chrome --filter_key search_term` |
| **Filter Records by value** | JSON | `dfindexeddb db -s SOURCE --format chrome --filter_value "search_term"` |


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

| Source | Type | Command |
| :--- | :--- | :--- |
| **LevelDB Folder** | Records | `dfleveldb db -s SOURCE` |
| **Log file** (.log) | Physical Records | `dfleveldb log -s SOURCE -t physical_records` |
| **Log file** (.log) | Blocks | `dfleveldb log -s SOURCE -t blocks` |
| **Log file** (.log) | Write Batches | `dfleveldb log -s SOURCE -t write_batches` |
| **Log file** (.log) | Internal Key Records | `dfleveldb log -s SOURCE -t parsed_internal_key` |
| **Table file** (.ldb) | Records | `dfleveldb ldb -s SOURCE -t record` |
| **Table file** (.ldb) | Blocks | `dfleveldb ldb -s SOURCE -t blocks` |
| **Descriptor** (MANIFEST) | Version Edits | `dfleveldb descriptor -s SOURCE -t versionedit` |

#### Optional Plugins

To apply a plugin parser for a leveldb file/folder, add the
`--plugin [Plugin Name]` argument.  Currently, there is support for the
following artifacts:

| Plugin Name | Artifact Name |
| -------- | ------- |
| `ChromeNotificationRecord` | Chrome/Chromium Notifications |
