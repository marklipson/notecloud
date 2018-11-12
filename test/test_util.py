import unittest
from notecloud.util import *


class TestUtil(unittest.TestCase):

    def test_parse_note(self):
        r = parse_note("abc\ndef")
        assert r == {'raw': 'abc\ndef'}
        r = parse_note("abc\n\ndef")
        assert r == {'title': 'abc', 'raw': 'abc\n\ndef'}
        r = parse_note("folder: x\ntag: a\ntag: b\n\ncontent\ngoes\nhere")
        assert r == {'folder': 'x', 'tag': ['a', 'b'], 'raw': 'content\ngoes\nhere'}

    def test_note_filename(self):
        r = note_filename({})
        assert r is None
        r = note_filename({"title": "t"})
        assert r == "t"
        r = note_filename({"folder": "f"})
        assert r.startswith("f/")
        r = note_filename({"folder": "f", "title": "t"})
        assert r == "f/t"
        r = note_filename({"title": "a/b"})
        assert r == "a%2Fb"

    def test_random_name(self):
        assert len(random_name()) == 16
        assert random_name() != random_name()

    def test_parse_duration(self):
        assert parse_duration("1m") == 60
        assert parse_duration("0.5hr") == 1800
        assert parse_duration("1000s") == 1000
        assert parse_duration("1d") == 86400

    def test_parse_search_spec(self):
        s, _ = parse_search_spec("tag=x")
        assert s({"tag": ["x", "y"]}) is True
        assert s({"tag": ["y"]}) is False
        s, _ = parse_search_spec("tag=x, folder=f")
        assert s({"tag": ["x"]}) is False
        assert s({"tag": ["x"], "folder": "f"}) is True
        assert s({"tag": ["x"], "folder": "g"}) is False
        s, _ = parse_search_spec("words together")
        assert s({"raw": "some words together"}) is True
        assert s({"raw": "some words not together"}) is False
        s, _ = parse_search_spec("word1, word2")
        assert s({"raw": "word1 xxx word2"}) is True
        assert s({"raw": "word2 xxx word1"}) is True
        assert s({"raw": "word2 xxx word3"}) is False



