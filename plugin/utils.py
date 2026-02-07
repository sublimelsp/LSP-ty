from __future__ import annotations

import gzip
import io
import os
import re
import shutil
import tarfile
import urllib.request
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import IO, Any, Union

PathLike = Union[Path, str]


def decompress_buffer(buffer: IO[bytes], *, filename: str, dst_dir: PathLike) -> bool:
    """
    Decompress the tarball in the bytes IO object.

    :param      buffer:    The buffer bytes IO object
    :param      filename:  The filename used to determine the decompression method
    :param      dst_dir:   The destination dir

    :returns:   Successfully decompressed the tarball or not
    """

    def tar_safe_extract(
        tar: tarfile.TarFile,
        path: PathLike = ".",
        members: Iterable[tarfile.TarInfo] | None = None,
        *,
        numeric_owner: bool = False,
    ) -> None:
        path = Path(path).resolve()
        for member in tar.getmembers():
            member_path = (path / member.name).resolve()
            if path not in member_path.parents:
                raise Exception("Attempted Path Traversal in Tar File")

        tar.extractall(path, members, numeric_owner=numeric_owner)

    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    if re.search(r"\.tar(?:\.(bz2|gz|xz))?$", filename):
        with tarfile.open(fileobj=buffer, mode="r:*") as tar_f:
            tar_safe_extract(tar_f, dst_dir)
        return True

    if filename.endswith(".zip"):
        with zipfile.ZipFile(buffer) as zip_f:
            zip_f.extractall(dst_dir)
        return True

    return False


def decompress_file(tarball: PathLike, dst_dir: PathLike | None = None) -> bool:
    """
    Decompress the tarball file.

    :param      tarball:  The tarball
    :param      dst_dir:  The destination directory

    :returns:   Successfully decompressed the tarball or not
    """
    tarball = Path(tarball)
    dst_dir = Path(dst_dir) if dst_dir else tarball.parent

    with tarball.open("rb") as f:
        return decompress_buffer(f, filename=tarball.name, dst_dir=dst_dir)


def simple_urlopen(url: str, *, chunk_size: int = 512 * 1024) -> bytes:
    with urllib.request.urlopen(url) as resp:
        buffer = io.BytesIO()
        shutil.copyfileobj(resp, buffer, length=chunk_size)
        data = buffer.getvalue()
        if resp.info().get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    return data


def rmtree_ex(path: str | Path, ignore_errors: bool = False, **kwargs: Any) -> None:
    """
    Same with `shutil.rmtree` but with a workaround for long path on Windows.

    @see https://stackoverflow.com/a/14076169/4643765
    @see https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
    """
    if os.name == "nt" and (path := Path(path)).is_absolute():
        path = Rf"\\?\{path}"
    shutil.rmtree(path, ignore_errors, **kwargs)
