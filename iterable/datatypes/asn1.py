from __future__ import annotations

import typing

try:
    from pyasn1.codec.der import decoder, encoder
    from pyasn1.type import univ

    HAS_PYASN1 = True
except ImportError:
    HAS_PYASN1 = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class ASN1Iterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYASN1:
            raise ImportError("ASN.1 support requires 'pyasn1' package")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()

            try:
                # Try to decode as single ASN.1 structure
                asn1Object, rest = decoder.decode(content, asn1Spec=univ.Sequence())
                self.items = [self._asn1_to_dict(asn1Object)]
            except Exception:
                # Try parsing multiple structures
                self.items = []
                offset = 0
                while offset < len(content):
                    try:
                        asn1Object, consumed = decoder.decode(content[offset:], asn1Spec=univ.Sequence())
                        self.items.append(self._asn1_to_dict(asn1Object))
                        offset += consumed
                    except Exception:
                        break

            self.iterator = iter(self.items)
        else:
            self.items = []

    @staticmethod
    def id() -> str:
        return "asn1"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def _asn1_to_dict(self, obj):
        """Convert ASN.1 object to Python dict"""
        if isinstance(obj, univ.Sequence) or isinstance(obj, univ.Set):
            result = {}
            for idx, component in enumerate(obj):
                key = f"field_{idx}"
                if hasattr(component, "getName"):
                    key = component.getName() or key
                result[key] = self._asn1_to_dict(component)
            return result
        elif isinstance(obj, (univ.OctetString, univ.BitString)):
            try:
                return obj.asOctets().decode("utf-8")
            except Exception:
                return obj.asOctets().hex()
        elif isinstance(obj, (univ.Integer, univ.Real, univ.Boolean)):
            return int(obj)
        elif isinstance(obj, univ.Null):
            return None
        elif isinstance(obj, (univ.PrintableString, univ.IA5String, univ.UTF8String)):
            return str(obj)
        else:
            return str(obj)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single ASN.1 record"""
        row = next(self.iterator)
        self.pos += 1

        if isinstance(row, dict):
            return row
        else:
            return {"value": row}

    def write(self, record: Row) -> None:
        """Write single ASN.1 record"""
        # Convert dict to ASN.1 Sequence
        # This is a simplified conversion - real ASN.1 encoding requires schema
        from pyasn1.type import univ

        seq = univ.Sequence()
        for idx, (_key, value) in enumerate(record.items()):
            if isinstance(value, str):
                seq.setComponentByPosition(idx, univ.UTF8String(value))
            elif isinstance(value, int):
                seq.setComponentByPosition(idx, univ.Integer(value))
            elif isinstance(value, bool):
                seq.setComponentByPosition(idx, univ.Boolean(value))
            elif value is None:
                seq.setComponentByPosition(idx, univ.Null())
            else:
                seq.setComponentByPosition(idx, univ.UTF8String(str(value)))

        asn1_data = encoder.encode(seq)
        self.fobj.write(asn1_data)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk ASN.1 records"""
        for record in records:
            self.write(record)
