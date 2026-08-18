from iterable.datatypes.psv import PSVIterable, SSVIterable


def test_psv_read_write(tmp_path):
    """Test PSV (pipe-separated values) read and write"""
    test_data = [
        {"name": "Alice", "age": "30", "city": "New York"},
        {"name": "Bob", "age": "25", "city": "London"},
        {"name": "Charlie", "age": "35", "city": "Tokyo"},
    ]

    src = tmp_path / "data.psv"
    src.write_text("name|age|city\nAlice|30|New York\nBob|25|London\nCharlie|35|Tokyo\n", encoding="utf-8")

    reader = PSVIterable(str(src), mode="r")
    try:
        results = list(reader)
    finally:
        reader.close()

    assert len(results) == 3
    assert results[0]["name"] == "Alice"
    assert results[0]["age"] == "30"

    dest = tmp_path / "out.psv"
    writer = PSVIterable(str(dest), mode="w", keys=["name", "age", "city"])
    try:
        for record in test_data:
            writer.write(record)
    finally:
        writer.close()

    lines = dest.read_text(encoding="utf-8").splitlines()
    assert "name|age|city" in lines[0]
    assert "Alice|30|New York" in lines[1]


def test_ssv_read_write(tmp_path):
    """Test SSV (semicolon-separated values) read and write"""
    test_data = [{"name": "Alice", "age": "30", "city": "New York"}, {"name": "Bob", "age": "25", "city": "London"}]

    src = tmp_path / "data.ssv"
    src.write_text("name;age;city\nAlice;30;New York\nBob;25;London\n", encoding="utf-8")

    reader = SSVIterable(str(src), mode="r")
    try:
        results = list(reader)
    finally:
        reader.close()

    assert len(results) == 2
    assert results[0]["name"] == "Alice"

    dest = tmp_path / "out.ssv"
    writer = SSVIterable(str(dest), mode="w", keys=["name", "age", "city"])
    try:
        for record in test_data:
            writer.write(record)
    finally:
        writer.close()

    lines = dest.read_text(encoding="utf-8").splitlines()
    assert "name;age;city" in lines[0]
    assert "Alice;30;New York" in lines[1]


def test_psv_id():
    """Test PSV ID"""
    assert PSVIterable.id() == "psv"


def test_ssv_id():
    """Test SSV ID"""
    assert SSVIterable.id() == "ssv"


def test_psv_flatonly():
    """Test PSV is flat only"""
    assert PSVIterable.is_flatonly()


def test_ssv_flatonly():
    """Test SSV is flat only"""
    assert SSVIterable.is_flatonly()
