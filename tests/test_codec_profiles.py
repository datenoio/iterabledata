from iterable.codecs import BZIP2Codec, GZIPCodec, LZMACodec


def test_balanced_profile_and_explicit_level_precedence(tmp_path):
    balanced = GZIPCodec(str(tmp_path / "balanced.gz"), mode="w", options={"profile": "balanced"})
    assert balanced.profile == "balanced"
    assert balanced.compression_level == 6

    explicit = GZIPCodec(str(tmp_path / "explicit.gz"), mode="w", options={"profile": "fast", "compression_level": 9})
    assert explicit.profile == "fast"
    assert explicit.compression_level == 9


def test_invalid_profile_is_actionable(tmp_path):
    try:
        GZIPCodec(str(tmp_path / "bad.gz"), mode="w", options={"profile": "turbo"})
    except ValueError as exc:
        assert "fast" in str(exc) and "balanced" in str(exc)
    else:
        raise AssertionError("invalid profile should fail")


def test_profiles_apply_to_stdlib_codecs(tmp_path):
    bz2 = BZIP2Codec(str(tmp_path / "data.bz2"), mode="w", options={"profile": "fast"})
    xz = LZMACodec(str(tmp_path / "data.xz"), mode="w", options={"profile": "max"})
    assert bz2.compression_level == 1
    assert xz.compression_level == 9
