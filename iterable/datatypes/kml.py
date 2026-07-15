from __future__ import annotations

import typing
from collections import defaultdict
from typing import Any

import lxml.etree as etree

from ..base import BaseCodec, BaseFileIterable
from ..helpers.xmlsec import safe_parse
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


def extract_coordinates(elem):
    """Extract coordinates from KML geometry elements"""
    coords_elem = elem.find(".//{http://www.opengis.net/kml/2.2}coordinates")
    if coords_elem is not None and coords_elem.text:
        coords_str = coords_elem.text.strip()
        # Parse coordinates: "lon,lat,alt lon,lat,alt ..."
        coords = []
        for coord_str in coords_str.split():
            parts = coord_str.split(",")
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    alt = float(parts[2]) if len(parts) > 2 else None
                    if alt is not None:
                        coords.append([lon, lat, alt])
                    else:
                        coords.append([lon, lat])
                except ValueError:
                    continue
        return coords
    return None


def kml_to_geojson(elem):
    """Convert KML element to GeoJSON-like feature"""
    feature = {"type": "Feature", "properties": {}, "geometry": None}

    # Extract properties from ExtendedData or SimpleData
    extended_data = elem.find(".//{http://www.opengis.net/kml/2.2}ExtendedData")
    if extended_data is not None:
        for data in extended_data.findall(".//{http://www.opengis.net/kml/2.2}Data"):
            name = data.get("name")
            value_elem = data.find("{http://www.opengis.net/kml/2.2}value")
            if name and value_elem is not None:
                feature["properties"][name] = value_elem.text or ""

    # Extract name and description
    name_elem = elem.find(".//{http://www.opengis.net/kml/2.2}name")
    if name_elem is not None and name_elem.text:
        feature["properties"]["name"] = name_elem.text

    desc_elem = elem.find(".//{http://www.opengis.net/kml/2.2}description")
    if desc_elem is not None and desc_elem.text:
        feature["properties"]["description"] = desc_elem.text

    # Extract geometry
    point = elem.find(".//{http://www.opengis.net/kml/2.2}Point")
    linestring = elem.find(".//{http://www.opengis.net/kml/2.2}LineString")
    polygon = elem.find(".//{http://www.opengis.net/kml/2.2}Polygon")

    if point is not None:
        coords = extract_coordinates(point)
        if coords and len(coords) > 0:
            feature["geometry"] = {"type": "Point", "coordinates": coords[0]}
    elif linestring is not None:
        coords = extract_coordinates(linestring)
        if coords:
            feature["geometry"] = {"type": "LineString", "coordinates": coords}
    elif polygon is not None:
        outer_boundary = polygon.find(".//{http://www.opengis.net/kml/2.2}outerBoundaryIs")
        if outer_boundary is not None:
            coords = extract_coordinates(outer_boundary)
            if coords:
                feature["geometry"] = {"type": "Polygon", "coordinates": [coords]}

    return feature


class KMLIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        prefix_strip: bool = True,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        self.prefix_strip = prefix_strip
        self.reset()

    def reset(self):
        super().reset()
        self.features = []
        self.pos = 0

        if self.mode == "r":
            # Parse KML document
            try:
                tree = safe_parse(self.fobj)
                root = tree.getroot()

                # Find all Placemark elements (main feature container in KML)
                ns = {"kml": "http://www.opengis.net/kml/2.2"}
                placemarks = root.findall(".//kml:Placemark", ns)

                if not placemarks:
                    # Try without namespace
                    placemarks = root.findall(".//Placemark")

                for placemark in placemarks:
                    feature = kml_to_geojson(placemark)
                    if feature["geometry"] is not None:
                        self.features.append(feature)

                self.iterator = iter(self.features)
            except Exception:
                self.features = []
                self.iterator = iter(self.features)

    @staticmethod
    def id() -> str:
        return "kml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if hasattr(self, "features"):
            return len(self.features)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single KML feature"""
        feature = next(self.iterator)
        self.pos += 1
        return feature

    def write(self, record: Row) -> None:
        """Write single KML feature"""
        # Convert GeoJSON-like feature to KML Placemark
        if "type" not in record or record["type"] != "Feature":
            # Assume it's a feature if it has geometry
            if "geometry" in record:
                record = {"type": "Feature", "properties": record.get("properties", {}), "geometry": record["geometry"]}

        # Create Placemark element with namespace
        ns = "http://www.opengis.net/kml/2.2"
        placemark = etree.Element("{" + ns + "}Placemark")

        # Add name
        if "name" in record.get("properties", {}):
            name_elem = etree.SubElement(placemark, "{" + ns + "}name")
            name_elem.text = str(record["properties"]["name"])

        # Add description
        if "description" in record.get("properties", {}):
            desc_elem = etree.SubElement(placemark, "{" + ns + "}description")
            desc_elem.text = str(record["properties"]["description"])

        # Add geometry
        geometry = record.get("geometry", {})
        if geometry:
            geom_type = geometry.get("type")
            coords = geometry.get("coordinates", [])

            if geom_type == "Point" and coords:
                point = etree.SubElement(placemark, "{" + ns + "}Point")
                coords_elem = etree.SubElement(point, "{" + ns + "}coordinates")
                coords_elem.text = f"{coords[0]},{coords[1]}" + (f",{coords[2]}" if len(coords) > 2 else "")
            elif geom_type == "LineString" and coords:
                linestring = etree.SubElement(placemark, "{" + ns + "}LineString")
                coords_elem = etree.SubElement(linestring, "{" + ns + "}coordinates")
                coords_str = " ".join(f"{c[0]},{c[1]}" + (f",{c[2]}" if len(c) > 2 else "") for c in coords)
                coords_elem.text = coords_str
            elif geom_type == "Polygon" and coords:
                polygon = etree.SubElement(placemark, "{" + ns + "}Polygon")
                outer_boundary = etree.SubElement(polygon, "{" + ns + "}outerBoundaryIs")
                linear_ring = etree.SubElement(outer_boundary, "{" + ns + "}LinearRing")
                coords_elem = etree.SubElement(linear_ring, "{" + ns + "}coordinates")
                outer_ring = coords[0] if isinstance(coords[0], list) and len(coords) > 0 else coords
                coords_str = " ".join(f"{c[0]},{c[1]}" + (f",{c[2]}" if len(c) > 2 else "") for c in outer_ring)
                coords_elem.text = coords_str

        # Add ExtendedData for other properties
        if record.get("properties"):
            extended_data = etree.SubElement(placemark, "{" + ns + "}ExtendedData")
            for key, value in record["properties"].items():
                if key not in ["name", "description"]:
                    data = etree.SubElement(extended_data, "{" + ns + "}Data", name=str(key))
                    value_elem = etree.SubElement(data, "{" + ns + "}value")
                    value_elem.text = str(value)

        # Write to file
        if not hasattr(self, "root_written"):
            # Write KML header
            header = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'
            )
            self.fobj.write(header.encode("utf-8") if self.binary else header)
            self.root_written = True

        etree.indent(placemark, space="  ")
        xml_str = etree.tostring(placemark, encoding="unicode", pretty_print=True) + "\n"
        self.fobj.write(xml_str.encode("utf-8") if self.binary else xml_str)
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk KML features"""
        for record in records:
            self.write(record)

    def close(self):
        """Close file and write KML footer if writing"""
        if self.mode in ["w", "wr"] and hasattr(self, "root_written"):
            footer = "</Document>\n</kml>\n"
            self.fobj.write(footer.encode("utf-8") if self.binary else footer)
        super().close()
