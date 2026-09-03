# bb-fedora-images

Machinery that generates the `os_list.json` catalog of upstream Fedora images for
[bb-imager](https://github.com/beagleboard/bb-imager-rs).

No images are built here. This repository only describes images that the Fedora Project
already publishes.

**In short:** Fedora images are for doing Linux development *on* BeagleBoard.org boards. The
Debian images remain the images for *using* BeagleBoard.org boards.

## Why Fedora

Fedora has a much faster release cycle than stable-release distributions like Ubuntu, while
being far more predictable than a rolling release like Arch Linux. Combine that cadence with
Fedora's largely upstream-first development policy and you get ideal ground for development.

The two image families have different jobs. BeagleBoard.org's Debian images are the product
experience: they carry the kernels, patches, and tooling that make a board work out of the box
today, and they are what anyone who wants to *use* a board should reach for. The Fedora images
are aimed at people working on Linux itself — kernel, u-boot, device trees — where staying
close to upstream matters more than having everything already wired up.

That difference is the point. A downstream patch that never makes it upstream is easy to lose
track of: it keeps working, so nobody notices it was never sent. Because a Fedora image ships
close to upstream, anything that does not work on a BeagleBoard.org board with an unmodified
Fedora image is a *visible* gap — something to file, fix, and get merged upstream, after which
every distribution benefits, Debian images included. Making Fedora a first-class, one-click
option in bb-imager keeps those gaps in view, and promotes upstream-first development across
the wider Linux ecosystem.

## Non-goals

**This repository will never generate images.** No kickstart files, no osbuild manifests, no
patched kernels, no bundled u-boot. The images referenced by `os_list.json` are the official
Fedora release artifacts from `download.fedoraproject.org`, byte for byte, verified by the
checksums Fedora publishes.

If something is broken or missing on a BeagleBoard.org board, the fix belongs in Fedora or
further upstream — in the kernel, in u-boot, in the device tree. Building a patched image here
would recreate exactly the problem this repository exists to avoid.

## What it generates

`os_list.json` is a bb-imager catalog: one group entry with a `flasher` and a list of
selectable images.

## How it works

`main.py` does three things, none of which require downloading an image:

1. **Discover.** Fetch <https://fedoraproject.org/releases.json> and filter it — currently to
   version `44`, arch `aarch64`, variant `Spins`, subvariant `Minimal` (`minimal_filter`).
   The URL and checksum come straight out of Fedora's metadata.
2. **Date it.** An HTTP `HEAD` against the artifact, reading `Last-Modified` (`release_date`).
3. **Size it.** This is the interesting part. `extract_size` reads the last 12 bytes of the
   `.xz` file with a `Range: bytes=-12` request to get the stream footer, uses it to locate and
   range-read the xz index, then sums the uncompressed size of every record. Two small requests
   yield the exact extracted size of a 5.6 GB image without fetching any of it.

## Usage

```sh
./main.py
```

Writes `os_list.json` into the current directory. Python 3.9 or newer, standard library only —
nothing to install.

The generated `os_list.json` is gitignored on purpose. It is a build artifact derived entirely
from Fedora's metadata, so it is regenerated rather than committed.

## Publishing

Every push to `main` regenerates the catalog and publishes it as the `continuous-release`
release asset:

```
https://github.com/beagleboard/bb-fedora-images/releases/download/continuous-release/os_list.json
```

That is the URL bb-imager fetches, listed under `imager.remote_configs` in its `config.json`.

## A note on booting

Stock Fedora aarch64 images do not ship a bootloader for BeagleBoard.org boards, which is why
the entry uses the `SdCardNoBootloader` flasher. Both the bb-imager GUI and CLI write the
appropriate bootloader to the correct partition themselves, so there is nothing extra to do
when flashing with bb-imager. If you write the image by hand instead, supplying u-boot is up to you.

## Supported images

Today: Fedora 44 Minimal (aarch64), offered for `beagle-am67`.

The intent is to grow this — further Fedora releases, more variants than Minimal, and more
board IDs as upstream support for them lands.

## Contributing

Sign your commits off with a `Signed-off-by:` trailer (`git commit -s`), matching the DCO
convention used across the BeagleBoard.org projects.
