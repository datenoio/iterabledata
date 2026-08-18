# Core formats (always available - no optional dependencies)
from .annotatedcsv import AnnotatedCSVIterable
from .apachelog import ApacheLogIterable
from .csv import CSVIterable
from .csvw import CSVWIterable
from .fwf import FixedWidthIterable
from .geojsonseq import GeoJSONSeqIterable
from .json import JSONIterable
from .jsonl import JSONLinesIterable
from .jsonld import JSONLDIterable
from .libsvm import LIBSVMIterable
from .ltsv import LTSVIterable
from .mysqldump import MySQLDumpIterable
from .psv import PSVIterable, SSVIterable
from .tar import TARIterable
from .txt import TxtIterable

# Optional formats - import conditionally
try:
    from .arff import ARFFIterable
except ImportError:
    pass

try:
    from .dot import DOTIterable
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
    from .bam import BAMIterable
except ImportError:
    pass

try:
    from .genomic_vcf import GenomicVCFIterable
except ImportError:
    pass

try:
    from .cram import CRAMIterable
except ImportError:
    pass

try:
    from .bed import BEDIterable
except ImportError:
    pass

try:
    from .genomic_intervals import GFF3Iterable, GTFIterable
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
    from .ducklake import DuckLakeIterable
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
    from .fasta import FASTAIterable
except ImportError:
    pass

try:
    from .fastq import FASTQIterable
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
    from .geoparquet import GeoParquetIterable
except ImportError:
    pass

try:
    from .flatgeobuf import FlatGeobufIterable
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
    from .gexf import GEXFIterable
except ImportError:
    pass

try:
    from .graphml import GraphMLIterable
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
    from .paimon import PaimonTableIterable
except ImportError:
    pass

try:
    from .paimon_mosaic import PaimonMosaicIterable
except ImportError:
    pass

try:
    from .paimon_row import PaimonRowIterable
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
    from .n3 import N3Iterable
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
    from .pcap import PCAPIterable
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
    from .otlp import OTLPJSONIterable, OTLPProtobufIterable
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
    from .sam import SAMIterable
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
    from .trig import TriGIterable
except ImportError:
    pass

try:
    from .trix import TriXIterable
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
    from .xlsb import XLSBIterable
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
    from .zarr import ZarrIterable
except ImportError:
    pass

try:
    from .asciigrid import ASCIIGridIterable
except ImportError:
    pass

try:
    from .bag import BAGIterable
except ImportError:
    pass

try:
    from .cif import CIFIterable
except ImportError:
    pass

try:
    from .czml import CZMLIterable
except ImportError:
    pass

try:
    from .e00 import E00Iterable
except ImportError:
    pass

try:
    from .edi import EDIIterable
except ImportError:
    pass

try:
    from .filegdb import FileGDBIterable
except ImportError:
    pass

try:
    from .fst import FSTIterable
except ImportError:
    pass

try:
    from .grib2 import GRIB2Iterable
except ImportError:
    pass

try:
    from .hdt import HDTIterable
except ImportError:
    pass

try:
    from .iati import IATIIterable
except ImportError:
    pass

try:
    from .las import LASIterable
except ImportError:
    pass

try:
    from .lotus123 import Lotus123Iterable
except ImportError:
    pass

try:
    from .mat import MATIterable
except ImportError:
    pass

try:
    from .mdb import AccessMDBIterable
except ImportError:
    pass

try:
    from .mif import MapInfoIterable
except ImportError:
    pass

try:
    from .mseed import MiniSEEDIterable
except ImportError:
    pass

try:
    from .pdb import PDBIterable
except ImportError:
    pass

try:
    from .segy import SEGYIterable
except ImportError:
    pass

try:
    from .webdataset import WebDatasetIterable
except ImportError:
    pass

try:
    from .xyz import XYZIterable
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
    "GeoJSONSeqIterable",
    "JSONIterable",
    "JSONLinesIterable",
    "JSONLDIterable",
    "LIBSVMIterable",
    "LTSVIterable",
    "MySQLDumpIterable",
    "PSVIterable",
    "SSVIterable",
    "TARIterable",
    "TxtIterable",
    # Optional formats
    "ARFFIterable",
    "ArrowIterable",
    "ASN1Iterable",
    "AVROIterable",
    "BAMIterable",
    "GenomicVCFIterable",
    "CRAMIterable",
    "BEDIterable",
    "GFF3Iterable",
    "GTFIterable",
    "BeamIterable",
    "BencodeIterable",
    "BSONIterable",
    "CapnpIterable",
    "CBORIterable",
    "CDFIterable",
    "CDXIterable",
    "CEFIterable",
    "DBFIterable",
    "DeltaIterable",
    "DOTIterable",
    "DuckDBIterable",
    "DuckLakeIterable",
    "DXFIterable",
    "EDNIterable",
    "EMLIterable",
    "FASTAIterable",
    "FASTQIterable",
    "FlatBuffersIterable",
    "FlexBuffersIterable",
    "FlinkIterable",
    "FeedIterable",
    "GELIterable",
    "GeoJSONIterable",
    "GEXFIterable",
    "GraphMLIterable",
    "GeoPackageIterable",
    "GeoParquetIterable",
    "FlatGeobufIterable",
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
    "PaimonTableIterable",
    "PaimonMosaicIterable",
    "PaimonRowIterable",
    "LDIFIterable",
    "MBOXIterable",
    "MessagePackIterable",
    "MHTMLIterable",
    "MVTIterable",
    "N3Iterable",
    "NQuadsIterable",
    "NTriplesIterable",
    "NetCDFIterable",
    "NumPyIterable",
    "ODSIterable",
    "ORCIterable",
    "ParquetIterable",
    "PCAPIterable",
    "PGCopyIterable",
    "PickleIterable",
    "ProtobufIterable",
    "OTLPJSONIterable",
    "OTLPProtobufIterable",
    "PulsarIterable",
    "PXIterable",
    "RDataIterable",
    "RDFXMLIterable",
    "RDSIterable",
    "RecordIOIterable",
    "SASIterable",
    "SAMIterable",
    "SequenceFileIterable",
    "ShapefileIterable",
    "SMILEIterable",
    "SPSSIterable",
    "SQLiteIterable",
    "StataIterable",
    "TFRecordIterable",
    "ThriftIterable",
    "TOMLIterable",
    "TopoJSONIterable",
    "TriGIterable",
    "TriXIterable",
    "TurtleIterable",
    "UBJSONIterable",
    "VCFIterable",
    "VortexIterable",
    "ZarrIterable",
    "WARCIterable",
    "XLSIterable",
    "XLSBIterable",
    "XLSXIterable",
    "XMLIterable",
    "YAMLIterable",
    "ZIPXMLSource",
    "ASCIIGridIterable",
    "BAGIterable",
    "CIFIterable",
    "CZMLIterable",
    "E00Iterable",
    "EDIIterable",
    "FileGDBIterable",
    "FSTIterable",
    "GRIB2Iterable",
    "HDTIterable",
    "IATIIterable",
    "LASIterable",
    "Lotus123Iterable",
    "MATIterable",
    "AccessMDBIterable",
    "MapInfoIterable",
    "MiniSEEDIterable",
    "PDBIterable",
    "SEGYIterable",
    "WebDatasetIterable",
    "XYZIterable",
]
