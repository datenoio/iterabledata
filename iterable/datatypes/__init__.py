# Core formats (always available - no optional dependencies)
from .annotatedcsv import AnnotatedCSVIterable
from .apachelog import ApacheLogIterable
from .csv import CSVIterable
from .csvw import CSVWIterable
from .fwf import FixedWidthIterable
from .json import JSONIterable
from .jsonl import JSONLinesIterable
from .jsonld import JSONLDIterable
from .libsvm import LIBSVMIterable
from .ltsv import LTSVIterable
from .mysqldump import MySQLDumpIterable
from .psv import PSVIterable, SSVIterable
from .txt import TxtIterable

# Optional formats - import conditionally
try:
    from .arff import ARFFIterable
except ImportError:
    pass

try:
    from .duckdb import DuckDBIterable
except ImportError:
    # duckdb not available
    pass

try:
    from .dxf import DXFIterable  # noqa: F401
except ImportError:
    pass

try:
    from .arrow import ArrowIterable
except ImportError:
    pass

try:
    from .asn1 import ASN1Iterable
except ImportError:
    pass

try:
    from .avro import AVROIterable
except ImportError:
    pass

try:
    from .beam import BeamIterable
except ImportError:
    pass

try:
    from .bencode import BencodeIterable
except ImportError:
    pass

try:
    from .bsonf import BSONIterable
except ImportError:
    pass

try:
    from .capnp import CapnpIterable
except ImportError:
    pass

try:
    from .cbor import CBORIterable
except ImportError:
    pass

try:
    from .cdf import CDFIterable  # noqa: F401
except ImportError:
    pass

try:
    from .cdx import CDXIterable
except ImportError:
    pass

try:
    from .cef import CEFIterable
except ImportError:
    pass

try:
    from .dbf import DBFIterable
except ImportError:
    pass

try:
    from .delta import DeltaIterable
except ImportError:
    pass

try:
    from .edn import EDNIterable
except ImportError:
    pass

try:
    from .eml import EMLIterable
except ImportError:
    pass

try:
    from .flatbuffers import FlatBuffersIterable
except ImportError:
    pass

try:
    from .flexbuffers import FlexBuffersIterable
except ImportError:
    pass

try:
    from .flink import FlinkIterable
except ImportError:
    pass

try:
    from .feed import FeedIterable  # noqa: F401
except ImportError:
    pass

try:
    from .gelf import GELIterable
except ImportError:
    pass

try:
    from .geojson import GeoJSONIterable
except ImportError:
    pass

try:
    from .html import HTMLIterable
except ImportError:
    pass

try:
    from .geopackage import GeoPackageIterable
except ImportError:
    pass

try:
    from .gml import GMLIterable
except ImportError:
    pass

try:
    from .hdf5 import HDF5Iterable
except ImportError:
    pass

try:
    from .numpy import NumPyIterable
except ImportError:
    pass

try:
    from .hocon import HOCONIterable
except ImportError:
    pass

try:
    from .hudi import HudiIterable
except ImportError:
    pass

try:
    from .ical import ICALIterable
except ImportError:
    pass

try:
    from .iceberg import IcebergIterable
except ImportError:
    pass

try:
    from .ilp import ILPIterable
except ImportError:
    pass

try:
    from .ini import INIIterable
except ImportError:
    pass

try:
    from .ion import IonIterable
except ImportError:
    pass

try:
    from .kafka import KafkaIterable
except ImportError:
    pass

try:
    from .kml import KMLIterable
except ImportError:
    pass

try:
    from .kmz import KMZIterable
except ImportError:
    pass

try:
    from .gpx import GPXIterable
except ImportError:
    pass

try:
    from .lance import LanceIterable
except ImportError:
    pass

try:
    from .ldif import LDIFIterable
except ImportError:
    pass

try:
    from .mbox import MBOXIterable
except ImportError:
    pass

try:
    from .mhtml import MHTMLIterable
except ImportError:
    pass

try:
    from .mvt import MVTIterable  # noqa: F401
except ImportError:
    pass

try:
    from .msgpack import MessagePackIterable
except ImportError:
    pass

try:
    from .nquads import NQuadsIterable
except ImportError:
    pass

try:
    from .ntriples import NTriplesIterable
except ImportError:
    pass

try:
    from .netcdf import NetCDFIterable  # noqa: F401
except ImportError:
    pass

try:
    from .ods import ODSIterable
except ImportError:
    pass

try:
    from .orc import ORCIterable
except ImportError:
    pass

try:
    from .parquet import ParquetIterable
except ImportError:
    pass

try:
    from .pgcopy import PGCopyIterable
except ImportError:
    pass

try:
    from .picklef import PickleIterable
except ImportError:
    pass

try:
    from .protobuf import ProtobufIterable
except ImportError:
    pass

try:
    from .pulsar import PulsarIterable
except ImportError:
    pass

try:
    from .px import PXIterable
except ImportError:
    pass

try:
    from .rdata import RDataIterable
except ImportError:
    pass

try:
    from .rdfxml import RDFXMLIterable
except ImportError:
    pass

try:
    from .rds import RDSIterable
except ImportError:
    pass

try:
    from .recordio import RecordIOIterable
except ImportError:
    pass

try:
    from .sas import SASIterable
except ImportError:
    pass

try:
    from .sequencefile import SequenceFileIterable
except ImportError:
    pass

try:
    from .shapefile import ShapefileIterable
except ImportError:
    pass

try:
    from .smile import SMILEIterable
except ImportError:
    pass

try:
    from .spss import SPSSIterable
except ImportError:
    pass

try:
    from .sqlite import SQLiteIterable
except ImportError:
    pass

try:
    from .stata import StataIterable
except ImportError:
    pass

try:
    from .tfrecord import TFRecordIterable
except ImportError:
    pass

try:
    from .thrift import ThriftIterable
except ImportError:
    pass

try:
    from .toml import TOMLIterable
except ImportError:
    pass

try:
    from .topojson import TopoJSONIterable  # noqa: F401
except ImportError:
    pass

try:
    from .turtle import TurtleIterable
except ImportError:
    pass

try:
    from .ubjson import UBJSONIterable
except ImportError:
    pass

try:
    from .vcf import VCFIterable
except ImportError:
    pass

try:
    from .warc import WARCIterable
except ImportError:
    pass

try:
    from .xls import XLSIterable
except ImportError:
    pass

try:
    from .xlsx import XLSXIterable
except ImportError:
    pass

try:
    from .xml import XMLIterable
except ImportError:
    pass

try:
    from .yaml import YAMLIterable
except ImportError:
    pass

try:
    from .vortex import VortexIterable
except ImportError:
    pass

try:
    from .zipxml import ZIPXMLSource
except ImportError:
    pass

__all__ = [
    # Core formats
    "AnnotatedCSVIterable",
    "ApacheLogIterable",
    "CSVIterable",
    "CSVWIterable",
    "FixedWidthIterable",
    "JSONIterable",
    "JSONLinesIterable",
    "JSONLDIterable",
    "LIBSVMIterable",
    "LTSVIterable",
    "MySQLDumpIterable",
    "PSVIterable",
    "SSVIterable",
    "TxtIterable",
    # Optional formats
    "ARFFIterable",
    "ArrowIterable",
    "ASN1Iterable",
    "AVROIterable",
    "BeamIterable",
    "BencodeIterable",
    "BSONIterable",
    "CapnpIterable",
    "CBORIterable",
    "CDXIterable",
    "CEFIterable",
    "DBFIterable",
    "DeltaIterable",
    "DuckDBIterable",
    "EDNIterable",
    "EMLIterable",
    "FlatBuffersIterable",
    "FlexBuffersIterable",
    "FlinkIterable",
    "GELIterable",
    "GeoJSONIterable",
    "GeoPackageIterable",
    "GMLIterable",
    "GPXIterable",
    "HDF5Iterable",
    "HOCONIterable",
    "HTMLIterable",
    "HudiIterable",
    "ICALIterable",
    "IcebergIterable",
    "ILPIterable",
    "INIIterable",
    "IonIterable",
    "KafkaIterable",
    "KMLIterable",
    "KMZIterable",
    "LanceIterable",
    "LDIFIterable",
    "MBOXIterable",
    "MessagePackIterable",
    "MHTMLIterable",
    "NQuadsIterable",
    "NTriplesIterable",
    "NumPyIterable",
    "ODSIterable",
    "ORCIterable",
    "ParquetIterable",
    "PGCopyIterable",
    "PickleIterable",
    "ProtobufIterable",
    "PulsarIterable",
    "PXIterable",
    "RDataIterable",
    "RDFXMLIterable",
    "RDSIterable",
    "RecordIOIterable",
    "SASIterable",
    "SequenceFileIterable",
    "ShapefileIterable",
    "SMILEIterable",
    "SPSSIterable",
    "SQLiteIterable",
    "StataIterable",
    "TFRecordIterable",
    "ThriftIterable",
    "TOMLIterable",
    "TurtleIterable",
    "UBJSONIterable",
    "VCFIterable",
    "VortexIterable",
    "WARCIterable",
    "XLSIterable",
    "XLSXIterable",
    "XMLIterable",
    "YAMLIterable",
    "ZIPXMLSource",
]
