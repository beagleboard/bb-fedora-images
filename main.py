#!/bin/python3

import json
from pathlib import Path
import urllib.request
import datetime
import email.utils

LZMA_STREAM_HEADER_SIZE = 12
LZMA_FOOTER = b"YZ"

OS_LIST_PATH: Path = Path("os_list.json")
FEDORA_ICON = "https://upload.wikimedia.org/wikipedia/commons/4/41/Fedora_icon_%282021%29.svg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original"
FEDORA_RELEASE_JSON = "https://fedoraproject.org/releases.json"


def get_json(url: str):
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def get_from_end(url: str, n: int) -> bytes:
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"Range": f"bytes=-{n}"})
    ) as resp:
        return resp.read()


def os_image(
    name: str,
    description: str,
    devices: [str],
    image_download_sha256: str,
    url: str,
    release_date: str,
    extract_size: int,
):
    return {
        "name": name,
        "description": description,
        "icon": FEDORA_ICON,
        "url": url,
        "image_download_sha256": image_download_sha256,
        "extract_size": extract_size,
        "release_date": release_date,
        "devices": devices,
    }


def minimal_filter(x) -> bool:
    return (
        x["version"] == "44"
        and x["arch"] == "aarch64"
        and x["variant"] == "Spins"
        and x["subvariant"] == "Minimal"
    )


def release_date(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD")) as resp:
        date = resp.getheader("Last-Modified")
        parsed_date = email.utils.parsedate_to_datetime(date)
        return parsed_date.strftime("%Y-%m-%d")


def decode_var_int(buf: bytes) -> tuple[int, int]:
    assert len(buf) != 0
    num = 0

    for i, byte in enumerate(buf):
        assert i < 9
        num |= (byte & 0x7F) << (i * 7)
        if byte & 0x80 == 0:
            return num, i + 1


def extract_size(url: str, file_size: int):
    footer = get_from_end(url, LZMA_STREAM_HEADER_SIZE)
    assert footer[-2:] == LZMA_FOOTER
    backward_size = (int.from_bytes(footer[-8:-4], "little") + 1) * 4

    index_plus_footer = backward_size + LZMA_STREAM_HEADER_SIZE
    index = get_from_end(url, index_plus_footer)[:backward_size]
    assert index[0] == 0

    num_records, count = decode_var_int(index[1:])
    index = index[count + 1 :]

    total_size = 0
    block_size = 0
    for _ in range(num_records):
        unpadded_size, count = decode_var_int(index)
        index = index[count:]
        uncompressed_size, count = decode_var_int(index)
        index = index[count:]

        total_size += uncompressed_size
        block_size += (unpadded_size + 3) & ~3

    assert LZMA_STREAM_HEADER_SIZE + block_size + index_plus_footer == file_size
    return total_size


if __name__ == "__main__":
    data = []

    release_json = get_json(FEDORA_RELEASE_JSON)
    minimal_images = filter(minimal_filter, release_json)

    for item in minimal_images:
        img_url = item["link"]

        data.append(
            os_image(
                f"Fedora Minimal {item['version']}",
                "The smallest possible Fedora installation; no desktop environment",
                ["beagle-am67"],
                item["sha256"],
                img_url,
                release_date(img_url),
                extract_size(img_url, int(item["size"])),
            )
        )

    with OS_LIST_PATH.open("w") as fp:
        json.dump(
            {
                "os_list": [
                    {
                        "name": "Fedora Images",
                        "description": "Fedora Linux is an innovative platform for hardware, clouds, and containers, built with love by you.",
                        "icon": FEDORA_ICON,
                        "flasher": "SdCardNoBootloader",
                        "subitems": data,
                    }
                ]
            },
            fp,
        )
