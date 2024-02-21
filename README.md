# dfIndexeddb

dfindexeddb is an experimental Python tool for performing digital forensic
analysis of IndexedDB files.

It parses leveldb, IndexedDB and javascript structures from these files without
requiring native libraries.

The content of IndexedDB files is dependent on what a web application stores
locally/offline using the web browser's [IndexedDB API](https://www.w3.org/TR/IndexedDB/).  Examples of content might include:
* text from a text/source-code editor application,
* emails and contact information from an e-mail application,
* images and metadata from a photo gallery application

## Installation

### Linux

1. Install the snappy compression development package

```
    $ sudo apt install libsnappy-dev
```

2. Create a virutal environemnt and install the package

```
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r requirements.txt
    $ python setup.py install
```
