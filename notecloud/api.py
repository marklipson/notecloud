"""
Storage and retrieval of notes.
"""
import os
import re
import time
from notecloud import util


class API(object):
    def __init__(self, use_root=None):
        self._use_root = use_root

    @property
    def root_folder(self):
        """
        All content is stored in one folder.
        """
        if self._use_root:
            return self._use_root
        folder = os.path.expanduser("~/.notecloud")
        if not folder.endswith("/"):
            folder += "/"
        try:
            os.makedirs(folder)
        except Exception:
            pass
        return folder

    def new_note(self, content=""):
        """
        Create a new note.
        """
        uid = util.random_name()
        uid = self.write_note(uid, content)
        return uid

    def read_note(self, path):
        """
        Read note content.
        """
        full_path = os.path.join(self.root_folder, path + ".txt")
        if os.path.exists(full_path):
            with open(full_path) as f:
                return f.read()
        return ""

    def note_exists(self, path):
        """
        Check if note exists.
        """
        full_path = os.path.join(self.root_folder, path + ".txt")
        return os.path.exists(full_path)

    def write_note(self, path, content):
        """
        Save note content.  Content can override path, so stored path is returned.
        :returns:  Path where note was stored.
        """
        content = re.sub(r'[ \t]+', ' ', content)
        props = util.parse_note(content)
        path_from_props = util.note_filename(props)
        del_old = None
        if path_from_props and path_from_props != path and not self.note_exists(path_from_props):
            del_old = path
            path = path_from_props
        full_name = os.path.join(self.root_folder, path+".txt")
        folder = os.path.dirname(full_name)
        try:
            os.makedirs(folder)
        except Exception:
            pass
        with open(full_name, 'w') as f:
            f.write(content)
        if not content.strip():
            self.delete_note(path)
        if del_old:
            self.delete_note(del_old)
        return path

    def delete_note(self, path):
        """
        Delete a note.
        """
        full_path = os.path.join(self.root_folder, path + ".txt")
        if os.path.exists(full_path):
            os.remove(full_path)
        subfolder = os.path.dirname(full_path)
        if "/" in path and not os.listdir(subfolder):
            os.rmdir(subfolder)

    def search_notes(self, spec="", limit=20):
        """
        Search notes...
        :param spec:  See util.parse_search_spec()
        :return:  A [] of matching notes.
        """
        t_now = time.time()
        results = []
        matcher, highlights = util.parse_search_spec(spec)
        for path, dirs, files in os.walk(self.root_folder):
            for f in files:
                full = os.path.join(path, f)
                if not full.endswith(".txt"):
                    continue
                with open(full) as fR:
                    content = fR.read()
                    props = util.parse_note(content)
                    props["age"] = t_now - os.stat(full).st_mtime
                    if not matcher(props):
                        continue
                f_path = full[len(self.root_folder):-4]
                del props["raw"]
                results.append({"path": f_path, "content": content, "props": props})
        # sort by age
        results = list(sorted(results, key=lambda r:r["props"].get("age", 0)))
        results = results[:limit]
        return results, highlights
