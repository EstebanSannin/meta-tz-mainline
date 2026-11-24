# Getting started: upstream Torizon OS on Verdin iMX8MP

This guide installs the engineering release on a Verdin iMX8M Plus and shows, in a few commands, that the GPU,
the NPU, the video units and the ISI work with upstream software.

The release is Torizon OS built on mainline Linux 7.3.1, with Mesa and GStreamer from upstream plus our changes,
tuned for the i.MX 8M Plus. It uses no NXP downstream drivers: no `galcore`, no VX delegate, no Hantro `vsi`
libraries. It is for evaluation, not for products. [README.md](README.md) has the release notes.

| Hardware block | Upstream driver | What you get |
|---|---|---|
| GPU (Vivante GC7000UL) | etnaviv (kernel and Mesa) | OpenGL ES 3.1, OpenCL 3.0 (embedded profile) through rusticl |
| NPU (Vivante VIP8000) | etnaviv and Mesa Teflon | TensorFlow Lite delegate for quantized models |
| VPU decoders (Hantro G1, G2) | hantro, V4L2 stateless | H.264 and HEVC 1080p decoding |
| VPU encoder (VC8000E) | hantro (patch series), V4L2 stateless | H.264 1080p encoding |
| ISI | imx8-isi, V4L2 memory-to-memory | colour conversion and scaling |
| Display | imx-lcdif, HDMI | DRM/KMS, Wayland or GBM |

## What you need

- A Verdin iMX8M Plus **Quad** module. The QuadLite modules have no NPU and no VPU. Tested on Verdin iMX8M
  Plus Quad 4GB WB IT.
- A Dahlia or Verdin Development Board carrier board, connected to Ethernet with DHCP.
- A USB stick of 1 GB or more for the installer image.
- An HDMI monitor for the display demos. Everything else also works without a display.

## 1. Get the release

Download from the release page
[engineering-release-1](https://github.com/EstebanSannin/meta-tz-mainline/releases/tag/engineering-release-1):

| File | What it is |
|---|---|
| `torizon-docker-verdin-imx8mp-Tezi_8.0.0-devel-20261123173501+build.0.tar` | OS image for Toradex Easy Installer, 274 MB |
| `tz-upstream-imx8mp-3.tar.gz` | the base container, for boards without internet access (optional) |
| `SHA256SUMS` | checksums: `sha256sum -c SHA256SUMS` |

The containers are on Docker Hub:

- `samnite/tz-upstream-imx8mp:3`: the graphics, compute, NPU and video stack, a base for your applications;
- `samnite/tz-upstream-imx8mp-demo:1`: the same with the demos and the self-test of this guide.

## 2. Install it with Toradex Easy Installer

1. Unpack the archive on the USB stick (FAT32 or ext4):

   ```
   tar xf torizon-docker-verdin-imx8mp-Tezi_8.0.0-devel-20261123173501+build.0.tar -C /media/<stick>
   ```

   It makes one folder with `image.json` in it.
2. Start Toradex Easy Installer on the module. If the module does not start it already, load it over USB in
   recovery mode as described in Toradex's guide
   [Loading Toradex Easy Installer](https://developer.toradex.com/easy-installer/toradex-easy-installer/loading-toradex-easy-installer).
3. Plug in the USB stick. The installer lists **Torizon OS (UPSTREAM)** 8.0.0-devel-20261123173501. Select it,
   press Install and confirm. Installing takes a few minutes.
4. Reboot when the installer says it is done.

## 3. Log in

The board gets its address over DHCP and announces itself with mDNS as `verdin-imx8mp-<serial>.local`, where
`<serial>` is the 8-digit serial number on the module label. The user is `torizon` with password `torizon`;
change it with `passwd`.

```
ssh torizon@verdin-imx8mp-<serial>.local
```

Check that you run the release:

```
$ uname -r
7.3.1-8.0.0-devel-00018-g1dd50f6c1323
$ grep PRETTY_NAME /etc/os-release
PRETTY_NAME="Torizon OS Upstream 8.0.0-devel-20261123173501+build.0 (wrynose)"
```

## 4. Run the demo container

```
docker pull samnite/tz-upstream-imx8mp-demo:1
alias tz-demo='docker run --rm -it --privileged -v /dev:/dev -v /run/udev:/run/udev:ro samnite/tz-upstream-imx8mp-demo:1 tz-demo'
tz-demo info
```

`--privileged` and the two volumes give the container the GPU, the NPU, the video devices and the display.
`tz-demo` alone lists the commands. `tz-demo info` shows what the system reports:

```
Kernel:   7.3.1-8.0.0-devel-00018-g1dd50f6c1323
Mesa:     4ddbea6679e5, GStreamer: feabad2506ff
DRM:      /dev/dri/renderD128 etnaviv
OpenGL:   renderer: Vivante GC7000 rev 6204
OpenGL:   version: OpenGL ES 3.1 Mesa 27.0.0-devel
OpenCL:   Platform #0: rusticl
OpenCL:    `-- Device #0: Vivante GC7000 rev 6204
Video:    /dev/video0 nxp,imx8mm-vpu-g1-dec
Video:    /dev/video1 nxp,imx8mq-vpu-g2-dec
Video:    /dev/video2 nxp,imx8mp-vpu-vc8000e-enc
Video:    /dev/video3 mxc_isi.0.capture
Video:    /dev/video4 mxc_isi.1.capture
Video:    /dev/video5 mxc_isi.m2m
NPU:      Teflon delegate /opt/mesa/lib/libteflon.so
Display:  card1-HDMI-A-1
```

### Check everything: `tz-demo check`

Runs each test in turn (about 4 minutes) and ends with a table. Every line must say PASS. With HDMI connected,
the GPU test and the video playback show on the screen:

```
==================== summary ====================
gpu            PASS   glmark2 score 148 on card1-HDMI-A-1
opencl         PASS   15.77 GFLOPS, 6.74 GB/s (float4)
npu-classify   PASS   2.62 ms on the NPU, x13.7 faster than the CPU, top-1 same as the CPU
npu-detect     PASS   12.02 ms on the NPU, 2/2 CPU objects found by the NPU
decode-h264    PASS   300 of 300 frames, 185.9 fps (1080p)
decode-hevc    PASS   300 of 300 frames, 418.0 fps (1080p)
encode         PASS   HEVC -> H.264 1080p at 222.0 fps, 9.5 Mbit/s, decodes back
isi            PASS   YUY2 1080p -> NV12 720p, 300 of 300 frames at 132.2 fps
play           PASS   295 frames shown in 10.0 s, 0 dropped, on the display through the GPU
kernel         PASS  no GPU hang, no video or kernel errors
```

Without a display, the GPU line is an off-screen rendering test and there is no `play` line.

### Everything at once: `tz-demo all`

Runs all units together for 60 seconds (`tz-demo all 300` for five minutes):

- a camera-like 1080p30 chain: a live YUY2 test source goes through the ISI to NV12, the VC8000E encodes it to
  H.264, the G1 decodes it and the GPU shows it on the display;
- HEVC 1080p decoding on the G2, clip after clip, as fast as it goes;
- image classification on the NPU, every result checked against the CPU;
- OpenCL memory kernels on the GPU (clpeak).

At the end it checks the kernel log for GPU hangs and video errors:

```
Running everything at once for 60 s (video to card1-HDMI-A-1)
==================== summary ====================
camera-chain   PASS   1800 of 1800 frames at 21.3 fps, 0 dropped (ISI, encoder, decoder, glimagesink)
hevc-decode    PASS   19500 frames in 65 runs, 325 fps on average
npu-loop       PASS   7257 inferences, 121 per second, 7257/7257 same top-1 as the CPU
opencl         PASS   1 clpeak runs, last 1.21 GB/s (float4)
kernel         PASS  no GPU hang, no video or kernel errors
```

On HDMI the chain runs at about 21 fps while OpenCL shares the GPU: the GPU runs one job at a time, so the
display waits for the OpenCL kernels. Without a display the chain keeps 30 fps.

### One unit at a time

| Command | What it shows |
|---|---|
| `tz-demo gpu` | glmark2 (OpenGL ES 2.0 benchmark) full screen on HDMI, about 6 minutes, with a score at the end. Without a display: off-screen OpenGL ES rendering |
| `tz-demo cube` | kmscube, a spinning textured cube, on the display until Ctrl-C |
| `tz-demo opencl` | the OpenCL device and clpeak's compute and memory figures |
| `tz-demo npu` | MobileNet V1 classification and SSD MobileNet V2 detection of a test picture, on the CPU and on the NPU |
| `tz-demo decode` | H.264 and HEVC 1080p decoding, as fast as it goes |
| `tz-demo encode` | HEVC to H.264 1080p transcoding, then the result decoded back |
| `tz-demo isi` | 1080p YUY2 to 720p NV12 on the ISI |
| `tz-demo play [FILE]` | plays a video file on the display through the GPU; mount the file into the container with `-v` |

`tz-demo npu` prints:

```
MobileNet V1 on grace_hopper.bmp
  CPU:  36.03 ms   military uniform 0.86, mortarboard 0.03, Windsor tie 0.02
  NPU:   2.62 ms   military uniform 0.87, mortarboard 0.03, Windsor tie 0.02
RESULT npu-classify PASS 2.62 ms on the NPU, x13.7 faster than the CPU, top-1 same as the CPU

SSD MobileNet V2 on grace_hopper.bmp, score >= 0.5
  CPU:  58.79 ms   tie 0.77, person 0.77
  NPU:  12.02 ms   tie 0.80, person 0.77
RESULT npu-detect PASS 12.02 ms on the NPU, 2/2 CPU objects found by the NPU
```

Figures of this release on Verdin iMX8M Plus Quad 4GB:

| Unit | Test | Result |
|---|---|---|
| GPU | glmark2 full run, 1920x1080 on HDMI | score 119 |
| OpenCL | clpeak single precision / global memory (float4) | 15.8 GFLOPS / 6.7 GB/s |
| NPU | MobileNet V1 / SSD MobileNet V2, per picture | 2.6 ms / 12.0 ms (CPU: 36 ms / 59 ms) |
| Decoders | 1080p H.264 / HEVC | 186 / 418 fps |
| Encoder | 1080p H.264 from the test clip (camera video: 130 to 138 fps) | 222 fps |
| ISI | 1080p YUY2 to 720p NV12 | 132 fps |

The test clips are a generated test pattern. Camera video is harder to encode, so expect the lower figure for it.

## 5. Use the stack in your own container

Start from the base container. Its environment already selects the upstream Mesa and GStreamer, turns on compute
and sets the NPU options:

```
FROM samnite/tz-upstream-imx8mp:3
```

Run it with `--privileged -v /dev:/dev -v /run/udev:/run/udev:ro`, as above. The base container has no Python and
no TensorFlow Lite runtime; the [demo Dockerfile](containers/tz-upstream-imx8mp-demo/Dockerfile) shows how to add
them.

Play a video on HDMI:

```
gst-launch-1.0 filesrc location=video.mp4 ! qtdemux ! h264parse ! v4l2slh264dec ! glimagesink
```

Encode 1080p H.264 from a YUY2 source through the ISI. With `capture-io-mode=dmabuf-import` the ISI writes straight
into the encoder's buffers; without it every frame is copied and a live 1080p30 source cannot keep up:

```
gst-launch-1.0 <source> ! video/x-raw,format=YUY2,width=1920,height=1080 ! \
    v4l2convert capture-io-mode=dmabuf-import ! video/x-raw,format=NV12 ! \
    v4l2slh264enc rate-control=cbr bitrate=8000000 ! h264parse ! matroskamux ! filesink location=out.mkv
```

Decoders write padded frames. Sinks that take them as they are (`glimagesink`, `waylandsink`, `kmssink`,
`fakevideosink`) are fast; a plain `fakesink` or `appsink` without video meta makes the decoder copy each frame with
the CPU, at 20 to 50 fps for 1080p.

Run a TensorFlow Lite model on the NPU, in Python with `ai-edge-litert`:

```python
from ai_edge_litert.interpreter import Interpreter, load_delegate

npu = load_delegate("/opt/mesa/lib/libteflon.so")
interpreter = Interpreter("model.tflite", experimental_delegates=[npu])
```

The NPU runs quantized (int8 and uint8) models. Operations it does not support stay on the CPU. The first
inference compiles the model for the NPU and takes up to a second.

OpenCL: `clinfo` lists the device "Vivante GC7000 rev 6204" on the rusticl platform. OpenCL applications and
OpenCV's OpenCL path work without changes.

## Known limits

- The GPU runs one job at a time and cannot preempt it. Long OpenCL kernels hold it and the display waits.
- The kernel stops any single GPU draw that runs longer than 500 ms. Qt Quick 3D's runtime light-probe
  filtering and some Godot scenes hit it; bake light probes offline. OpenCL is not affected.
- glmark2 needs `--visual-config alpha=0` on this display (`tz-demo gpu` sets it): the display controller does not
  scan out frame buffers with alpha.
- No Vulkan, no HEVC encoding (the hardware has it, but there is no kernel interface for it yet).
- OpenCL reports the embedded profile.
- `systemd-networkd-wait-online` reports a failure at boot; the network works.

[README.md](README.md) has the full release notes, the test results and the source commits.
