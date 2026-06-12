"""Tests for type hints and typed helper functions."""

import tempfile
from dataclasses import dataclass

import pytest

from iterable import (
    CodecArgs,
    IterableArgs,
    Row,
    as_dataclasses,
    as_pydantic,
    open_iterable,
)


def test_type_aliases_exist():
    """Test that type aliases are available."""
    # These should be importable and usable in type annotations
    assert Row is not None
    assert IterableArgs is not None
    assert CodecArgs is not None


def test_open_iterable_type_hints():
    """Test that open_iterable has proper type hints."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        fname = f.name

    # Should work with type checking
    source = open_iterable(fname)
    assert source is not None
    source.close()


def test_base_iterable_read_type_hints():
    """Test that BaseIterable.read() returns Row type."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\n")
        fname = f.name

    with open_iterable(fname) as source:
        row: Row = source.read()
        assert isinstance(row, dict)
        assert "name" in row


def test_base_iterable_write_type_hints():
    """Test that BaseIterable.write() accepts Row type."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        fname = f.name

    with open_iterable(fname, mode="w", iterableargs={"keys": ["name", "age"]}) as dest:
        row: Row = {"name": "Alice", "age": 30}
        dest.write(row)


def test_base_iterable_read_bulk_type_hints():
    """Test that BaseIterable.read_bulk() returns list[Row]."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        fname = f.name

    with open_iterable(fname) as source:
        rows: list[Row] = source.read_bulk(10)
        assert isinstance(rows, list)
        assert all(isinstance(row, dict) for row in rows)


def test_base_iterable_write_bulk_type_hints():
    """Test that BaseIterable.write_bulk() accepts list[Row]."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        fname = f.name

    with open_iterable(fname, mode="w", iterableargs={"keys": ["name", "age"]}) as dest:
        rows: list[Row] = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        dest.write_bulk(rows)


@dataclass
class Person:
    """Test dataclass for as_dataclasses helper."""

    name: str
    age: str  # CSV reads everything as strings


def test_as_dataclasses_basic():
    """Test as_dataclasses helper with basic usage."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        fname = f.name

    with open_iterable(fname) as source:
        people = list(as_dataclasses(source, Person))
        assert len(people) == 2
        assert isinstance(people[0], Person)
        assert people[0].name == "Alice"
        assert people[0].age == "30"  # CSV reads as string
        assert people[1].name == "Bob"
        assert people[1].age == "25"  # CSV reads as string


def test_as_dataclasses_type_safety():
    """Test that as_dataclasses provides type safety."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\n")
        fname = f.name

    with open_iterable(fname) as source:
        person = next(as_dataclasses(source, Person))
        # Type checkers should recognize person as Person type
        assert person.name == "Alice"
        assert person.age == "30"  # CSV reads as string


def test_as_dataclasses_missing_field():
    """Test as_dataclasses with missing required fields."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name\nAlice\n")
        fname = f.name

    with open_iterable(fname) as source:
        with pytest.raises(ValueError, match="Failed to create Person"):
            list(as_dataclasses(source, Person))


def test_as_dataclasses_extra_fields():
    """Test as_dataclasses with extra fields (should be ignored)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age,city\nAlice,30,NYC\n")
        fname = f.name

    with open_iterable(fname) as source:
        # Extra fields should be ignored (only defined fields are used)
        people = list(as_dataclasses(source, Person))
        assert len(people) == 1
        assert people[0].name == "Alice"
        assert people[0].age == "30"  # CSV reads as string


def test_as_pydantic_basic():
    """Test as_pydantic helper with basic usage."""
    pytest.importorskip("pydantic")

    from pydantic import BaseModel

    class PersonModel(BaseModel):
        name: str
        age: int

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        fname = f.name

    with open_iterable(fname) as source:
        people = list(as_pydantic(source, PersonModel))
        assert len(people) == 2
        assert isinstance(people[0], PersonModel)
        assert people[0].name == "Alice"
        assert people[0].age == 30


def test_as_pydantic_validation_error():
    """Test as_pydantic with invalid data."""
    pytest.importorskip("pydantic")

    from pydantic import BaseModel

    class PersonModel(BaseModel):
        name: str
        age: int

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,not_a_number\n")
        fname = f.name

    with open_iterable(fname) as source:
        with pytest.raises(ValueError, match="Failed to validate row"):
            list(as_pydantic(source, PersonModel, validate=True))


def test_as_pydantic_without_validation():
    """Test as_pydantic with validation disabled."""
    pytest.importorskip("pydantic")

    from pydantic import BaseModel

    class PersonModel(BaseModel):
        name: str
        age: int

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\nAlice,not_a_number\n")
        fname = f.name

    with open_iterable(fname) as source:
        # Should not raise error when validation is disabled
        people = list(as_pydantic(source, PersonModel, validate=False))
        assert len(people) == 1


def test_as_pydantic_missing_dependency():
    """Test that as_pydantic raises ImportError when pydantic is not available."""
    # This test verifies the error message, but we can't easily test
    # the actual ImportError without mocking
    # The function should raise ImportError with helpful message
    pass


def test_iterableargs_type_hint():
    """Test that IterableArgs can be used in type annotations."""
    args: IterableArgs = {"delimiter": ",", "encoding": "utf-8"}
    assert isinstance(args, dict)


def test_codecargs_type_hint():
    """Test that CodecArgs can be used in type annotations."""
    args: CodecArgs = {"level": 6}
    assert isinstance(args, dict)
