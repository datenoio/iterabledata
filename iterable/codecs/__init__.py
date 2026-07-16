# Core codecs (always available)
from .bz2codec import BZIP2Codec
from .gzipcodec import GZIPCodec
from .lzmacodec import LZMACodec
from .profiles import PROFILE_LEVELS, PROFILES
from .rawcodec import RAWCodec
from .zipcodec import ZIPCodec

# Optional codecs - import conditionally
try:
    from .brotlicodec import BrotliCodec
except ImportError:
    # brotli_file not available
    BrotliCodec = None  # type: ignore[assignment, misc]

try:
    from .lz4codec import LZ4Codec
except ImportError:
    # lz4 not available
    LZ4Codec = None  # type: ignore[assignment, misc]

try:
    from .lzocodec import LZOCodec
except ImportError:
    # python-lzo not available
    LZOCodec = None  # type: ignore[assignment, misc]

try:
    from .snappycodec import SnappyCodec
except ImportError:
    # python-snappy not available
    SnappyCodec = None  # type: ignore[assignment, misc]

try:
    from .zstdcodec import ZSTDCodec
except ImportError:
    # zstandard not available
    ZSTDCodec = None  # type: ignore[assignment, misc]

try:
    from .szipcodec import SZipCodec
except ImportError:
    # py7zr not available
    SZipCodec = None  # type: ignore[assignment, misc]

__all__ = [
    "BZIP2Codec",
    "BrotliCodec",
    "GZIPCodec",
    "LZ4Codec",
    "LZMACodec",
    "LZOCodec",
    "RAWCodec",
    "SnappyCodec",
    "SZipCodec",
    "ZIPCodec",
    "ZSTDCodec",
    "PROFILES",
    "PROFILE_LEVELS",
]
