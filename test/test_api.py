import unittest
import tempfile
import shutil
from notecloud.api import API


class TestAPI(unittest.TestCase):
    def test_basics(self):
        tmpdir = tempfile.mkdtemp()
        api = API(tmpdir)
        assert api.root_folder == tmpdir
        n1 = api.new_note("abc")
        assert api.read_note(n1) == "abc"
        assert api.write_note(n1, "abc\ndef") == n1
        assert api.read_note(n1) == "abc\ndef"
        # rename
        assert api.write_note(n1, "title: abc\n\ncontent goes here") == "abc"
        assert api.write_note("abc", "folder: x\ntitle: abc\n\ncontent goes here") == "x/abc"
        # delete
        api.write_note("x/abc", "")
        assert len(api.search_notes(""))[0] == 0
        shutil.rmtree(tmpdir)

    def test_search(self):
        tmpdir = tempfile.mkdtemp()
        api = API(tmpdir)
        assert api.root_folder == tmpdir
        n1 = api.new_note("tag: a\n\nword1\nword3")
        n2 = api.new_note("tag: a\n\nword2\nword3")
        rr = api.search_notes("tag=a")[0]
        assert len(rr) == 2
        rr = api.search_notes("tag=b")[0]
        assert len(rr) == 0
        rr = api.search_notes("word1")[0]
        assert len(rr) == 1
        rr = api.search_notes("word2")[0]
        assert len(rr) == 1
        rr = api.search_notes("word3")[0]
        assert len(rr) == 2
        shutil.rmtree(tmpdir)
