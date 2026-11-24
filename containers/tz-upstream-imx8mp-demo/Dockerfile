# syntax=docker/dockerfile:1
#
# Demos and a self-test for the upstream graphics, compute, NPU and video stack on Verdin iMX8MP.
# Built on the tz-upstream-imx8mp container; adds glmark2, kmscube, clpeak, a TensorFlow Lite runtime,
# two Coral models, two generated 1080p test clips and the tz-demo script.
#
#   docker buildx build --platform linux/arm64 -t tz-upstream-imx8mp-demo:1 .
#   docker run --rm -it --privileged -v /dev:/dev -v /run/udev:/run/udev:ro tz-upstream-imx8mp-demo:1 tz-demo check

ARG BASE=samnite/tz-upstream-imx8mp:3
ARG CORAL=https://raw.githubusercontent.com/google-coral/test_data/104342d2d3480b3e66203073dac24f4e2dbb4c41
ARG TF=https://raw.githubusercontent.com/tensorflow/tensorflow/v2.18.0/tensorflow/lite/examples/label_image/testdata

# Test clips: 10 s of 1080p30 test pattern in H.264 and HEVC, made with ffmpeg (no third-party footage).
FROM ${BASE} AS clips
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN mkdir /clips && \
    ffmpeg -loglevel error -f lavfi -i testsrc2=size=1920x1080:rate=30 -t 10 -c:v libx264 -profile:v high \
        -pix_fmt yuv420p -b:v 8M /clips/h264-1080p30.mp4 && \
    ffmpeg -loglevel error -f lavfi -i testsrc2=size=1920x1080:rate=30 -t 10 -c:v libx265 -x265-params log-level=error \
        -pix_fmt yuv420p -b:v 6M -tag:v hvc1 /clips/hevc-1080p30.mp4

FROM ${BASE} AS models
ARG CORAL
ARG TF
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /models
RUN for f in mobilenet_v1_1.0_224_quant.tflite ssd_mobilenet_v2_coco_quant_postprocess.tflite \
        imagenet_labels.txt coco_labels.txt; do curl -fsSLO "$CORAL/$f"; done && \
    curl -fsSLO "$TF/grace_hopper.bmp" && \
    printf '%s\n' \
        "2d0ebfa2e75ae93c709e9ecc27570c9c0e49b7780733a840f82589fc1272fc3d  mobilenet_v1_1.0_224_quant.tflite" \
        "42fb3d70ffb7bb37dd518f730f7be784b831c2078f30c497d0019cc2e987fa26  ssd_mobilenet_v2_coco_quant_postprocess.tflite" \
        "b8aaeb5630c62626a7d124a05c0e14230a7ffdd2136a31d0190a4fb71c1d82f1  imagenet_labels.txt" \
        "dc183f003fc753c4c43fae6fdf7f387559449573f13fa32e517fb7453fd380f1  coco_labels.txt" \
        "8c1165a143b3ac5c37fba13a918101133d549d3419c7fc474ae70a2f29263b80  grace_hopper.bmp" | sha256sum -c

FROM ${BASE}
RUN apt-get update && apt-get install -y --no-install-recommends \
        glmark2-es2-drm kmscube clpeak mesa-utils-bin python3 python3-venv python3-pil procps && \
    rm -rf /var/lib/apt/lists/*
RUN python3 -m venv --system-site-packages /opt/demo/venv && \
    /opt/demo/venv/bin/pip install --no-cache-dir ai-edge-litert==2.4.0 numpy==2.5.5
COPY --from=clips /clips /opt/demo/clips
COPY --from=models /models/grace_hopper.bmp /opt/demo/
COPY --from=models /models/*.tflite /models/*.txt /opt/demo/models/
COPY npu.py /opt/demo/
COPY tz-demo /usr/local/bin/
CMD ["tz-demo", "help"]
