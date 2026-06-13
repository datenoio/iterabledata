import datetime
import logging
from copy import copy

import bson

from .utils import get_dict_value_deep

OTYPES_MAP = [
    [str, "string"],
    [str, "string"],
    [datetime.datetime, "datetime"],
    [int, "integer"],
    [bool, "boolean"],
    [float, "float"],
    [str, "string"],
    [bson.int64.Int64, "integer"],
    [bson.objectid.ObjectId, "string"],
    [type([]), "array"],
]


def merge_schemes(alist, novalue=True):
    """Merges schemes of list of objects and generates final data schema"""
    if len(alist) == 0:
        return None
    obj = alist[0]
    okeys = obj.keys()
    for item in alist[1:]:
        for k in item.keys():
            #            print(obj[k]['type'])
            if k not in okeys:
                obj[k] = item[k]
            elif obj[k]["type"] in ["integer", "float", "string", "datetime"]:
                if not novalue:
                    obj[k]["value"] += item[k]["value"]
            elif obj[k]["type"] == "dict":
                if not novalue:
                    obj[k]["value"] += item[k]["value"]
                if "schema" in item[k].keys():
                    obj[k]["schema"] = merge_schemes([obj[k]["schema"], item[k]["schema"]])
            elif obj[k]["type"] == "array":
                #                if 'subtype' not in obj[k].keys():
                #                   logging.info(str(obj[k]))
                if "subtype" in obj[k].keys() and obj[k]["subtype"] == "dict":
                    if not novalue:
                        obj[k]["value"] += item[k]["value"]
                    if "schema" in item[k].keys():
                        obj[k]["schema"] = merge_schemes([obj[k]["schema"], item[k]["schema"]])
                else:
                    if not novalue:
                        obj[k]["value"] += item[k]["value"]
    return obj


def get_schemes(alist):
    """Generates schemas for each object"""
    results = []
    for o in alist:
        results.append(get_schema(o))
    return results


def get_schema(obj: dict, novalue=True):
    """Generates schema from object"""
    result = {}
    for k in obj.keys():
        if obj[k] is None:
            result[k] = {"type": "string", "value": 1}
        elif isinstance(obj[k], str):
            result[k] = {"type": "string", "value": 1}
        elif isinstance(obj[k], datetime.datetime):
            result[k] = {"type": "datetime", "value": 1}
        elif isinstance(obj[k], bool):
            result[k] = {"type": "boolean", "value": 1}
        elif isinstance(obj[k], float):
            result[k] = {"type": "float", "value": 1}
        elif isinstance(obj[k], int):
            result[k] = {"type": "integer", "value": 1}
        elif isinstance(obj[k], bson.int64.Int64):
            result[k] = {"type": "integer", "value": 1}
        elif isinstance(obj[k], bson.objectid.ObjectId):
            result[k] = {"type": "string", "value": 1}
        elif isinstance(obj[k], dict):
            result[k] = {"type": "dict", "value": 1, "schema": get_schema(obj[k])}
        elif isinstance(obj[k], list):
            result[k] = {"type": "array", "value": 1}
            if len(obj[k]) == 0:
                result[k]["subtype"] = "string"
            else:
                found = False
                for otype, oname in OTYPES_MAP:
                    if isinstance(obj[k][0], otype):
                        result[k]["subtype"] = oname
                        found = True
                if not found:
                    if isinstance(obj[k][0], dict):
                        result[k]["subtype"] = "dict"
                        result[k]["schema"] = merge_schemes(get_schemes(obj[k]))
                    else:
                        logging.info(f"Unknown object {k} type {str(type(obj[k][0]))}")
        else:
            logging.info(f"Unknown object {k} type {str(type(obj[k]))}")
            result[k] = {"type": "string", "value": 1}
        if novalue:
            del result[k]["value"]
    return result


def extract_keys_from_dict(obj: dict, parent: str = None, text: str = None, level: int = 1):
    """Extracts keys from object"""
    if text is None:
        text = ""
    if not parent:
        text = "'schema': {\n"
    for k in obj.keys():
        if isinstance(obj[k], dict):
            text += "\t" * level + f"'{k}' : {{'type' : 'dict', 'schema' : {{\n"
            text += extract_keys_from_dict(obj[k], k, text, level + 1)
            text += "\t" * level + "}},\n"
        elif isinstance(obj[k], list):
            text += "\t" * level + f"'{k}' : {{'type' : 'list', 'schema' : {{ 'type' : 'dict', 'schema' : {{\n"
            if len(obj[k]) > 0:
                item = obj[k][0]
                if isinstance(item, dict):
                    text += extract_keys_from_dict(item, k, text, level + 1)
                else:
                    text += "\t" * level + f"'{k}' : {{'type' : 'string'}},\n"
            text += "\t" * level + "}}},\n"
        else:
            logging.info(str(type(obj[k])))
            text += "\t" * level + f"'{k}' : {{'type' : 'string'}},\n"
    if not parent:
        text += "}"
    return text


def schema_from_list_of_dicts(data: list[dict]):
    """Generates schema from python dictionary"""
    scheme = None
    for r in data:
        if scheme is None:
            scheme = get_schema(r)
        else:
            scheme = merge_schemes([scheme, get_schema(r)])
    return scheme


def schema2fieldslist(schema: dict, prefix: str = None, predefined: dict = None, sample: dict = None):
    """Converts data schema to the fields list"""
    fieldslist = []
    for k in schema.keys():
        if prefix is None:
            name = k
        else:
            name = ".".join([".".join(prefix.split(".")), k])
        try:
            sampledata = get_dict_value_deep(sample, name) if sample else ""
        except Exception:
            sampledata = ""
        if "schema" not in schema[k].keys():
            if schema[k]["type"] != "array":
                field = {"name": name, "type": schema[k]["type"], "description": "", "sample": sampledata, "class": ""}
            else:
                subtype = schema[k].get("subtype", "any")
                field = {
                    "name": name,
                    "type": f"list of [{subtype}]",
                    "description": "",
                    "sample": sampledata,
                    "class": "",
                }
            if predefined:
                if name in predefined.keys():
                    field["description"] = predefined[name]["text"]
                    if predefined[name]["class"]:
                        field["class"] = predefined[name]["class"]
                elif k in predefined.keys():
                    field["description"] = predefined[k]["text"]
                    if predefined[k]["class"]:
                        field["class"] = predefined[k]["class"]
            if field["type"] == "datetime":
                field["class"] = "datetime"
            fieldslist.append(field)
        else:
            if prefix is not None:
                subprefix = copy(prefix) + "." + k
            #                subprefix.append(k)
            else:
                subprefix = k
            if schema[k]["type"] == "dict":
                field = {"name": name, "type": schema[k]["type"], "description": "", "sample": "", "class": ""}
                if predefined:
                    if name in predefined.keys():
                        field["description"] = predefined[name]["text"]
                        if predefined[name]["class"]:
                            field["class"] = predefined[name]["class"]
                    elif k in predefined.keys():
                        field["description"] = predefined[k]["text"]
                        if predefined[k]["class"]:
                            field["class"] = predefined[k]["class"]
                fieldslist.append(field)
                fieldslist.extend(
                    schema2fieldslist(schema[k]["schema"], prefix=subprefix, predefined=predefined, sample=sample)
                )
            elif schema[k]["type"] == "array":
                subtype = schema[k].get("subtype", "any")
                field = {"name": name, "type": f"list of [{subtype}]", "description": "", "sample": "", "class": ""}
                if predefined:
                    if name in predefined.keys():
                        field["description"] = predefined[name]["text"]
                        if predefined[name]["class"]:
                            field["class"] = predefined[name]["class"]
                    elif k in predefined.keys():
                        field["description"] = predefined[k]["text"]
                        if predefined[k]["class"]:
                            field["class"] = predefined[k]["class"]
                fieldslist.append(field)
                fieldslist.extend(schema2fieldslist(schema[k]["schema"], prefix=subprefix, sample=sample))
    return fieldslist
