# Upstream Torizon OS for Verdin iMX8MP: engineering release 1

Experimental. Torizon OS on mainline Linux 7.3.1, plus a container with upstream Mesa and GStreamer and our
changes. For evaluation, not for products.

## What is in it

**OS image** (`torizon-docker`, distro `torizon-upstream`, this layer):

- Linux 7.3.1 stable with the patches in `recipes-kernel/linux/linux-toradex-upstream-7.3/tz-upstream`:
  - VC8000E H.264 encoder: Paul Kocialkowski's series v1, at 500 MHz as in the NXP BSP;
  - ISI enabled on Verdin: memory-to-memory scaling and colour conversion (`v4l2convert`);
  - etnaviv holds a CPU latency request while the GPU or NPU is busy (`qos_latency_us`, default 100).
- U-Boot pinned to v2026.10 (2027.01-rc1 hangs in SPL on this board).
- GPU hang check: stock 500 ms (see Known limits).

**Container** `tz-upstream-imx8mp:3` (`containers/tz-upstream-imx8mp/Dockerfile`, arm64, built on Debian sid snapshot
20261115T000000Z: LLVM 22.1.8, SPIRV-LLVM-Translator 22.1.0, the toolchain the OpenCL work was validated with):

- Mesa in `/opt/mesa`: etnaviv with OpenGL ES 3.1, OpenCL 3.0 embedded profile (with 64-bit integers, half
  precision and OpenGL sharing) through rusticl, and the Teflon TensorFlow Lite delegate for the NPU
  (`/opt/mesa/lib/libteflon.so`).
- Mesa's libclc in `/usr/lib/clc`: Debian's cannot link `fma()`.
- GStreamer in `/opt/gst`: `v4l2slh264dec`, `v4l2slh265dec`, `v4l2slh264enc`, `v4l2convert` (ISI),
  `glimagesink` on GBM with zero-copy NV12, `kmssink`, `waylandsink`.
- The image environment selects these builds and turns on compute (`ETNA_EXPERIMENTAL_COMPUTE=1`,
  `RUSTICL_ENABLE=etnaviv`) and the NPU settings of the evaluation (`ETNA_*`, `TEFLON_*`). All of them are
  opt-in in this Mesa.

**Demo container** `tz-upstream-imx8mp-demo:1` (`containers/tz-upstream-imx8mp-demo`): the same plus glmark2, kmscube,
clpeak, a TensorFlow Lite runtime, two Coral models, test clips and `tz-demo`, which shows and checks each unit.
[GETTING-STARTED.md](GETTING-STARTED.md) installs the release and runs it.

Container `:3` replaces `:2`, which gave wrong NPU results: with compute on, the container's default, Teflon's jobs
went to the GPU (Mesa commit 4ddbea6679 fixes it).

## Use

Flash the Tezi image with Toradex Easy Installer, then pull the container on the board:

```
docker pull samnite/tz-upstream-imx8mp:3
```

or load it from the release archive with `docker load -i tz-upstream-imx8mp-3.tar.gz` (the image is then
named `tz-upstream-imx8mp:3`).

Run it with the devices:

```
docker run --rm -it --privileged -v /dev:/dev -v /run/udev:/run/udev:ro samnite/tz-upstream-imx8mp:3 clinfo
```

Play a video on HDMI:

```
gst-launch-1.0 filesrc location=video.mp4 ! qtdemux ! h264parse ! v4l2slh264dec ! glimagesink
```

Encode 1080p H.264:

```
gst-launch-1.0 ... ! video/x-raw,format=NV12,width=1920,height=1080 ! v4l2slh264enc rate-control=cbr bitrate=8000000 ! h264parse ! ...
```

Feed a YUYV or RGB source through the ISI to the encoder. At 1080p, `capture-io-mode=dmabuf-import` avoids a
copy per frame:

```
... ! v4l2convert capture-io-mode=dmabuf-import ! video/x-raw,format=NV12 ! v4l2slh264enc ! ...
```

For the NPU, install a TensorFlow Lite runtime (for example `ai-edge-litert`) and load
`/opt/mesa/lib/libteflon.so` as an external delegate.

## Tested

On a Verdin iMX8MP with Dahlia, with the image and the container (23 November 2026):

- OpenGL ES 3.1: dEQP-GLES31 must-pass list, 16,008 pass, no failures, no GPU hangs.
- OpenCL: Khronos CTS run inside the container, all pass with no GPU hangs: basic 431/431, images 44/44,
  half/select/geometrics/vectors 52/52, integer_ops 76/76, conversions (wimpy) 900/900 sub-tests, bruteforce (wimpy)
  92/92. clpeak and OpenCV's OpenCL path give the same figures as the development build.
- NPU: six Coral models with the container's Mesa and environment (24 November, container `:3`), every result
  matches the CPU. Faster than NXP's driver on all six against
  Torizon OS 8, and on five of six against 7.7.0 (SSD MobileNet V2 is 5% slower).
- `tz-demo check` and `tz-demo all` pass with container `:3`, on HDMI and without a display (24 November).
- Video: H.264 / HEVC 1080p decode at 209 / 402 fps. H.264 encode at 129–138 fps at 4–15 Mbit/s. Both codecs play
  on HDMI at 30 fps with no drops and an exact picture. ISI to encoder works.

## Known limits

- The kernel's 500 ms GPU hang check stops single draws that run longer, for example Qt Quick 3D's runtime light
  probe filtering and some Godot scenes. Bake Qt light probes offline. OpenCL is not affected: Mesa splits long
  launches.
- The GPU runs one job at a time and cannot preempt it: long OpenCL kernels hold it and the display waits. With
  clpeak's compute test running, a 30 fps video on HDMI drops to about 5 fps.
- No Vulkan. No HEVC encode: the hardware has it, but there is no kernel interface for it yet.
- OpenCL reports the embedded profile; NXP reports the full profile.
- The container is Debian sid, not the trixie base of Torizon's own containers.
- `systemd-networkd-wait-online` fails at boot (seen since the first upstream builds); the network works.

## Sources

| Part | Repository, branch | Commit |
|---|---|---|
| Yocto layer | github.com/EstebanSannin/meta-tz-mainline `tz-upstream/imx8mp` | this commit |
| Linux | github.com/EstebanSannin/linux `tz-upstream/imx8mp` | 3a11102d65 |
| Mesa | github.com/EstebanSannin/mesa `tz-upstream/imx8mp` | 4ddbea6679 |
| GStreamer | github.com/EstebanSannin/gstreamer `tz-upstream/imx8mp` | feabad2506 |
| libclc | gitlab.freedesktop.org/karolherbst/mesa-libclc, tag 22.1.8.3 | 87f6600724 |
