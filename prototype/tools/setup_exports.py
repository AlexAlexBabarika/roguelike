"""Install Linux/Web templates from the official release using HTTP byte ranges.

ZIP CRCs validate extracted entries. Range reads avoid downloading the 1.3 GB
archive of every platform. Requires Python 3, no third-party packages.
"""

import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://github.com/godotengine/godot/releases/download/4.5.1-stable/Godot_v4.5.1-stable_export_templates.tpz"
DESTINATION = Path.home() / ".local/share/godot/export_templates/4.5.1.stable"
NAMES = ("web_nothreads_release.zip", "web_nothreads_debug.zip", "linux_release.x86_64")


class RemoteArchive(io.RawIOBase):
    def __init__(self):
        super().__init__()
        with urllib.request.urlopen(urllib.request.Request(URL, method="HEAD"), timeout=60) as response:
            self.url = response.geturl()
            self.length = int(response.headers["Content-Length"])
        self.position = 0

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        if whence == 0:
            self.position = offset
        elif whence == 1:
            self.position += offset
        elif whence == 2:
            self.position = self.length + offset
        return self.position

    def tell(self):
        return self.position

    def read(self, size=-1):
        remaining = self.length - self.position
        size = min(size if size >= 0 else remaining, remaining)
        if size <= 0:
            return b""
        request = urllib.request.Request(
            self.url, headers={"Range": f"bytes={self.position}-{self.position + size - 1}"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 206:
                raise RuntimeError("Server ignored byte ranges; install the official templates manually")
            data = response.read(size)
        self.position += len(data)
        return data


if __name__ == "__main__":
    DESTINATION.mkdir(parents=True, exist_ok=True)
    with RemoteArchive() as remote, zipfile.ZipFile(remote) as archive:
        for name in NAMES:
            destination = DESTINATION / name
            if destination.exists():
                print("Already installed:", name)
                continue
            data = archive.read("templates/" + name)
            temporary = destination.with_suffix(destination.suffix + ".partial")
            temporary.write_bytes(data)
            temporary.replace(destination)
            print("Installed official template:", name)
