"""
Monkeypatch for undetected_chromedriver on Python 3.12+ where distutils was removed.
Import this BEFORE importing undetected_chromedriver.
"""
import sys
import types

if "distutils" not in sys.modules:
    distutils_mod = types.ModuleType("distutils")
    version_mod   = types.ModuleType("distutils.version")

    class LooseVersion:
        def __init__(self, vstring):
            import re
            self.vstring = str(vstring)
            self.version = [
                int(x) if x.isdigit() else x
                for x in re.split(r"(\d+)", self.vstring)
                if x
            ]

        def __str__(self):
            return self.vstring

        def __repr__(self):
            return f"LooseVersion ('{self.vstring}')"

        def _cmp(self, other):
            if self.version == other.version:
                return 0
            return -1 if self.version < other.version else 1

        def __lt__(self, other): return self._cmp(other) < 0
        def __le__(self, other): return self._cmp(other) <= 0
        def __gt__(self, other): return self._cmp(other) > 0
        def __ge__(self, other): return self._cmp(other) >= 0
        def __eq__(self, other): return self._cmp(other) == 0

    version_mod.LooseVersion = LooseVersion
    distutils_mod.version    = version_mod
    sys.modules["distutils"]         = distutils_mod
    sys.modules["distutils.version"] = version_mod
