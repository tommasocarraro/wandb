import base64
import hashlib
from os import PathLike
from typing import NewType, Union

ETag = NewType("ETag", str)
HexMD5 = NewType("HexMD5", str)
B64MD5 = NewType("B64MD5", str)


def md5_string(string: str) -> B64MD5:
    return _b64_from_hasher(hashlib.md5(string.encode()))


def _b64_from_hasher(hasher: "hashlib._Hash") -> B64MD5:
    return B64MD5(base64.b64encode(hasher.digest()).decode("ascii"))


def b64_to_hex_id(string: B64MD5) -> HexMD5:
    return HexMD5(base64.standard_b64decode(string).hex())


def hex_to_b64_id(encoded_string: Union[str, bytes]) -> B64MD5:
    if isinstance(encoded_string, bytes):
        encoded_string = encoded_string.decode("utf-8")
    return base64.standard_b64encode(bytes.fromhex(encoded_string)).decode("utf-8")


def md5_file_b64(*paths: PathLike) -> B64MD5:
    return _b64_from_hasher(_md5_file_hasher(*paths))


def md5_file_hex(*paths: PathLike) -> HexMD5:
    return HexMD5(_md5_file_hasher(*paths).hexdigest())


def _md5_file_hasher(*paths: PathLike) -> "hashlib._Hash":
    hash_md5 = hashlib.md5()
    for path in sorted(paths):
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(64 * 1024), b""):
                hash_md5.update(chunk)
    return hash_md5
