# PyInstaller runtime hook to fix stdout/stderr for windowless apps
# This runs BEFORE the main script
import sys
import io

class NullStream(io.StringIO):
    """A stream that discards everything and properly reports isatty()."""
    def write(self, s):
        pass
    
    def flush(self):
        pass
    
    def isatty(self):
        return False

class NullInputStream(io.StringIO):
    """A null input stream."""
    def read(self, n=-1):
        return ''
    
    def readline(self):
        return ''
    
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = NullStream()
if sys.stderr is None:
    sys.stderr = NullStream()
if sys.stdin is None:
    sys.stdin = NullInputStream()

