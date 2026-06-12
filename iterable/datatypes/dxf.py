from __future__ import annotations

import typing

try:
    import ezdxf

    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, ReadError, WriteNotSupportedError


class DXFIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_EZDXF:
            raise ImportError("DXF support requires 'ezdxf' package")

        self.options = options
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # ezdxf requires a filename
            if self.filename:
                try:
                    self.doc = ezdxf.readfile(self.filename)
                except Exception as e:
                    raise FormatParseError(
                        format_id="dxf",
                        message=f"Failed to read DXF file: {e}",
                        filename=self.filename,
                    ) from e
            elif hasattr(self.fobj, "name"):
                try:
                    self.doc = ezdxf.readfile(self.fobj.name)
                except Exception as e:
                    raise FormatParseError(
                        format_id="dxf",
                        message=f"Failed to read DXF file: {e}",
                        filename=getattr(self.fobj, "name", None),
                    ) from e
            else:
                # Try to read from stream
                try:
                    self.doc = ezdxf.read(self.fobj)
                except Exception as e:
                    raise ReadError(
                        message=f"Failed to read DXF from stream: {e}",
                        filename=self.filename,
                    ) from e

            self.iterator = self.__iterator()
        else:
            raise WriteNotSupportedError("dxf", "DXF writing is not yet implemented")

    def __iterator(self):
        """Iterator for reading DXF entities"""
        # Iterate through all entities in modelspace
        msp = self.doc.modelspace()

        for entity in msp:
            entity_dict = {
                "dxftype": entity.dxftype(),
                "layer": entity.dxf.layer if hasattr(entity.dxf, "layer") else None,
                "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
            }

            # Extract geometry based on entity type
            if entity.dxftype() == "LINE":
                entity_dict["start"] = tuple(entity.dxf.start) if hasattr(entity.dxf, "start") else None
                entity_dict["end"] = tuple(entity.dxf.end) if hasattr(entity.dxf, "end") else None
            elif entity.dxftype() == "CIRCLE":
                entity_dict["center"] = tuple(entity.dxf.center) if hasattr(entity.dxf, "center") else None
                entity_dict["radius"] = entity.dxf.radius if hasattr(entity.dxf, "radius") else None
            elif entity.dxftype() == "ARC":
                entity_dict["center"] = tuple(entity.dxf.center) if hasattr(entity.dxf, "center") else None
                entity_dict["radius"] = entity.dxf.radius if hasattr(entity.dxf, "radius") else None
                entity_dict["start_angle"] = entity.dxf.start_angle if hasattr(entity.dxf, "start_angle") else None
                entity_dict["end_angle"] = entity.dxf.end_angle if hasattr(entity.dxf, "end_angle") else None
            elif entity.dxftype() == "POINT":
                entity_dict["location"] = tuple(entity.dxf.location) if hasattr(entity.dxf, "location") else None
            elif entity.dxftype() == "TEXT":
                entity_dict["text"] = entity.dxf.text if hasattr(entity.dxf, "text") else None
                entity_dict["insert"] = tuple(entity.dxf.insert) if hasattr(entity.dxf, "insert") else None
                entity_dict["height"] = entity.dxf.height if hasattr(entity.dxf, "height") else None
            elif entity.dxftype() == "LWPOLYLINE":
                # Lightweight polyline
                try:
                    entity_dict["points"] = [tuple(p) for p in entity.get_points("xy")]
                    entity_dict["closed"] = entity.closed
                except Exception:
                    entity_dict["points"] = None
            elif entity.dxftype() == "POLYLINE":
                try:
                    entity_dict["points"] = [tuple(v.dxf.location) for v in entity.vertices]
                    entity_dict["closed"] = entity.is_closed
                except Exception:
                    entity_dict["points"] = None

            # Add handle for reference
            if hasattr(entity.dxf, "handle"):
                entity_dict["handle"] = entity.dxf.handle

            yield entity_dict

    @staticmethod
    def id() -> str:
        return "dxf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self):
        if hasattr(self, "doc"):
            try:
                msp = self.doc.modelspace()
                return len(list(msp))
            except Exception:
                return 0
        return 0

    def close(self):
        if hasattr(self, "doc"):
            self.doc.close()
        super().close()

    def read(self, skip_empty: bool = True) -> dict:
        entity = next(self.iterator)
        self.pos += 1
        return entity
