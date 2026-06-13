"""Typed helper functions for type-safe data processing."""

import dataclasses
from collections.abc import Iterator

from ..base import BaseIterable
from ..types import T


def as_dataclasses(
    iterable: BaseIterable,
    dataclass_type: type[T],
    skip_empty: bool = True,
) -> Iterator[T]:
    """Convert dict-based rows from an iterable into dataclass instances.

    Args:
        iterable: The iterable to read rows from
        dataclass_type: The dataclass type to convert rows to
        skip_empty: Whether to skip empty rows (passed to iterable.read())

    Yields:
        Instances of the specified dataclass type

    Example:
        >>> from dataclasses import dataclass
        >>> from iterable import open_iterable, as_dataclasses
        >>>
        >>> @dataclass  # doctest: +SKIP
        >>> class Person:  # doctest: +SKIP
        ...     name: str
        ...     age: int
        ...
        >>> with open_iterable('people.csv') as source:  # doctest: +SKIP
        ...     for person in as_dataclasses(source, Person):
        ...         print(person.name, person.age)
    """
    # Get dataclass field names
    field_names = {f.name for f in dataclasses.fields(dataclass_type)}

    for row in iterable:
        if skip_empty and not row:
            continue
        try:
            # Filter row to only include dataclass fields
            filtered_row = {k: v for k, v in row.items() if k in field_names}
            yield dataclass_type(**filtered_row)
        except TypeError as e:
            raise ValueError(f"Failed to create {dataclass_type.__name__} from row: {row}. Error: {e}") from e


def as_pydantic(
    iterable: BaseIterable,
    model_type: type[T],
    skip_empty: bool = True,
    validate: bool = True,
) -> Iterator[T]:
    """Convert dict-based rows from an iterable into Pydantic model instances.

    Args:
        iterable: The iterable to read rows from
        model_type: The Pydantic model type to convert rows to
        skip_empty: Whether to skip empty rows (passed to iterable.read())
        validate: Whether to validate rows against the model schema

    Yields:
        Instances of the specified Pydantic model type

    Raises:
        ImportError: If pydantic is not installed
        ValidationError: If validation is enabled and a row doesn't match the schema

    Example:
        >>> from pydantic import BaseModel
        >>> from iterable import open_iterable, as_pydantic
        >>>
        >>> class Person(BaseModel):  # doctest: +SKIP
        ...     name: str
        ...     age: int
        ...
        >>> with open_iterable('people.csv') as source:  # doctest: +SKIP
        ...     for person in as_pydantic(source, Person):
        ...         print(person.name, person.age)
    """
    try:
        from pydantic import BaseModel, ValidationError
    except ImportError as e:
        raise ImportError("Pydantic is required for as_pydantic(). Install it with: pip install pydantic>=2.0.0") from e

    if not issubclass(model_type, BaseModel):
        raise TypeError(f"{model_type.__name__} must be a Pydantic BaseModel subclass")

    for row in iterable:
        if skip_empty and not row:
            continue
        try:
            if validate:
                yield model_type.model_validate(row)
            else:
                yield model_type.model_construct(**row)
        except ValidationError as e:
            raise ValueError(f"Failed to validate row against {model_type.__name__}: {row}. Error: {e}") from e
