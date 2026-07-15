from __future__ import annotations

import typing
from collections import defaultdict
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.xmlsec import safe_iterparse
from ..types import Row


def etree_to_dict(t, prefix_strip=True):
    """Converts tree of XML elements from lxml to python dictionary"""
    tag = t.tag if not prefix_strip else t.tag.rsplit("}", 1)[-1]
    d = {tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                if prefix_strip:
                    k = k.rsplit("}", 1)[-1]
                dd[k].append(v)
        d = {tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[tag].update(("@" + k.rsplit("}", 1)[-1], v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            tag = tag.rsplit("}", 1)[-1]
            if text:
                d[tag]["#text"] = text
        else:
            d[tag] = text
    return d


def parse_rdf_description(elem, prefix_strip=True):
    """Parse RDF Description element into a triple-like structure"""
    result = {}

    # Get about/resource attribute (subject)
    subject = None
    if "about" in elem.attrib:
        subject = elem.attrib["about"]
    elif "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about" in elem.attrib:
        subject = elem.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"]
    elif "resource" in elem.attrib:
        subject = elem.attrib["resource"]
    elif "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource" in elem.attrib:
        subject = elem.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]

    if subject:
        result["subject"] = subject
        result["subject_type"] = "uri"
    else:
        # Blank node
        result["subject"] = f"_:bnode_{id(elem)}"
        result["subject_type"] = "bnode"

    # Parse properties (predicates and objects)
    triples = []
    for child in elem:
        child.tag.rsplit("}", 1)[-1] if "}" in child.tag else child.tag
        predicate_uri = child.tag if not prefix_strip else child.tag.rsplit("}", 1)[-1]

        # Get object
        obj = None
        obj_type = "literal"
        obj_datatype = None
        obj_language = None

        if "resource" in child.attrib:
            obj = child.attrib["resource"]
            obj_type = "uri"
        elif "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource" in child.attrib:
            obj = child.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]
            obj_type = "uri"
        elif child.text:
            obj = child.text.strip()
            obj_type = "literal"
            # Check for datatype
            if "datatype" in child.attrib:
                obj_datatype = child.attrib["datatype"]
            elif "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}datatype" in child.attrib:
                obj_datatype = child.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}datatype"]
            # Check for language
            if "lang" in child.attrib:
                obj_language = child.attrib["lang"]
            elif "{http://www.w3.org/XML/1998/namespace}lang" in child.attrib:
                obj_language = child.attrib["{http://www.w3.org/XML/1998/namespace}lang"]
        elif len(child) > 0:
            # Nested RDF structure
            obj = f"_:bnode_{id(child)}"
            obj_type = "bnode"

        if obj is not None:
            triple = {
                "predicate": predicate_uri,
                "predicate_type": "uri",
                "object": obj,
                "object_type": obj_type,
            }
            if obj_datatype:
                triple["object_datatype"] = obj_datatype
            if obj_language:
                triple["object_language"] = obj_language
            triples.append(triple)

    result["triples"] = triples
    return result


class RDFXMLIterable(BaseFileIterable):
    """
    RDF/XML format reader/writer.
    RDF/XML is a specific XML format for representing RDF data.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        tagname: str | None = None,
        prefix_strip: bool = True,
        parse_as_triples: bool = True,
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize RDF/XML iterable.

        Args:
            tagname: Tag name to iterate over (default: 'Description' or 'rdf:Description')
            prefix_strip: Strip XML namespace prefixes (default: True)
            parse_as_triples: Parse as RDF triples instead of XML structure (default: True)
        """
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        self.tagname = tagname
        self.prefix_strip = prefix_strip
        self.parse_as_triples = parse_as_triples
        if "tagname" in options:
            self.tagname = options["tagname"]
        if "prefix_strip" in options:
            self.prefix_strip = options["prefix_strip"]
        if "parse_as_triples" in options:
            self.parse_as_triples = options["parse_as_triples"]

        if self.tagname is None:
            # Default to RDF Description elements
            self.tagname = "Description"

        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.reader = safe_iterparse(self.fobj)
        self.pos = 0

    @staticmethod
    def id() -> str:
        return "rdfxml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single RDF/XML record"""
        row = None
        while not row:
            try:
                event, elem = next(self.reader)
                shorttag = elem.tag.rsplit("}", 1)[-1]

                # Check if this is an RDF Description element
                if shorttag == self.tagname or shorttag == "rdf:" + self.tagname or elem.tag.endswith("}Description"):
                    if self.parse_as_triples:
                        # Parse as RDF triples
                        row = parse_rdf_description(elem, self.prefix_strip)
                    else:
                        # Parse as regular XML
                        if self.prefix_strip:
                            row = etree_to_dict(elem, self.prefix_strip)
                        else:
                            row = etree_to_dict(elem)
                        # Extract the Description content
                        if self.tagname in row:
                            row = row[self.tagname]
                        elif "Description" in row:
                            row = row["Description"]
            except StopIteration:
                raise StopIteration from None

        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single RDF/XML record"""
        # This is a simplified writer - full RDF/XML writing is complex
        # For now, we'll write as XML with RDF structure
        import xml.etree.ElementTree as ET

        if self.parse_as_triples and "triples" in record:
            # Write as RDF triples
            subject = record.get("subject", "_:bnode")
            subject_type = record.get("subject_type", "uri")

            # Create RDF Description element
            if subject_type == "uri":
                desc_attrib = {"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about": subject}
            else:
                desc_attrib = {"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}nodeID": subject}

            desc = ET.Element("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description", desc_attrib)

            # Add triples as child elements
            for triple in record.get("triples", []):
                pred = triple.get("predicate", "")
                obj = triple.get("object", "")
                obj_type = triple.get("object_type", "literal")

                child = ET.SubElement(desc, pred)
                if obj_type == "uri":
                    child.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", obj)
                else:
                    child.text = obj
                    if triple.get("object_datatype"):
                        child.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}datatype", triple["object_datatype"])
                    if triple.get("object_language"):
                        child.set("{http://www.w3.org/XML/1998/namespace}lang", triple["object_language"])

            # Write XML
            xml_str = ET.tostring(desc, encoding="unicode")
            self.fobj.write(xml_str.encode("utf-8"))
            self.fobj.write(b"\n")
        else:
            # Write as regular XML
            import xml.etree.ElementTree as ET

            root = ET.Element("rdf:RDF", {"xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"})
            desc = ET.SubElement(root, "rdf:Description")
            for key, value in record.items():
                if key not in ["subject", "subject_type", "triples"]:
                    child = ET.SubElement(desc, key)
                    child.text = str(value)
            xml_str = ET.tostring(root, encoding="unicode")
            self.fobj.write(xml_str.encode("utf-8"))
            self.fobj.write(b"\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk RDF/XML records"""
        for record in records:
            self.write(record)
