# syntax=docker/dockerfile:1
#
# Upstream graphics and media stack for Verdin iMX8MP on mainline Linux (engineering release).
#
#   Mesa (tz-upstream/imx8mp): etnaviv with OpenGL ES 3.1, OpenCL 3.0 (embedded profile) through rusticl,
#   and the Teflon TensorFlow Lite delegate for the NPU. Mesa's libclc, which rusticl needs.
#   GStreamer (tz-upstream/imx8mp): main with the GL on GBM fixes and the V4L2 stateless H.264 encoder.
#
# Everything is built on one pinned Debian sid snapshot, the toolchain the OpenCL work was validated with,
# from a dated sid image older than the snapshot (apt cannot downgrade a newer base).
# Mesa goes to /opt/mesa and GStreamer to /opt/gst; the environment below makes applications use them.
#
#   docker buildx build --platform linux/arm64 -t tz-upstream-imx8mp:3 .
#   docker run --rm -it --privileged -v /dev:/dev -v /run/udev:/run/udev:ro tz-upstream-imx8mp:3 clinfo
#
# To build from local source trees instead of GitHub, override the source stages:
#   --build-context mesa-src=<mesa tree> --build-context gst-src=<gstreamer tree>

ARG SNAPSHOT=20261115T000000Z
ARG MESA_REPO=https://github.com/EstebanSannin/mesa.git
ARG MESA_COMMIT=4ddbea6679e539022fa49755aaa8807dfdd98e58
ARG GST_REPO=https://github.com/EstebanSannin/gstreamer.git
ARG GST_COMMIT=feabad2506ff3c48475523a0f5620a55b51df157
ARG LIBCLC_REF=22.1.8.3

FROM debian:sid-20261104 AS base
ARG SNAPSHOT
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${SNAPSHOT} sid main" \
        > /etc/apt/sources.list && \
    echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80retries

FROM base AS git
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

FROM git AS mesa-src
ARG MESA_REPO
ARG MESA_COMMIT
RUN git clone --filter=blob:none --no-checkout "$MESA_REPO" /src && git -C /src checkout -q "$MESA_COMMIT" && \
    git -C /src log -1 --format="%H %cs" > /src/.commit && rm -rf /src/.git

FROM git AS gst-src
ARG GST_REPO
ARG GST_COMMIT
RUN git clone --filter=blob:none --no-checkout "$GST_REPO" /src && git -C /src checkout -q "$GST_COMMIT" && \
    git -C /src log -1 --format="%H %cs" > /src/.commit && rm -rf /src/.git

# Mesa's patched libclc: Debian's libclc implements fma() with a function only Mesa's copy provides,
# so every OpenCL kernel that calls fma() fails to link with it.
FROM git AS libclc
ARG LIBCLC_REF
RUN apt-get update && apt-get install -y --no-install-recommends cmake ninja-build python3 \
        clang-22 llvm-22-dev llvm-spirv-22 libclang-22-dev && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch ${LIBCLC_REF} https://gitlab.freedesktop.org/karolherbst/mesa-libclc.git /src && \
    cmake -S /src -B /build -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER=clang-22 -DCMAKE_CXX_COMPILER=clang++-22 \
        -DLLVM_DIR=/usr/lib/llvm-22/lib/cmake/llvm -DLLVM_SPIRV=/usr/bin/llvm-spirv-22 \
        -DLIBCLC_TARGETS_TO_BUILD="spirv-mesa3d-;spirv64-mesa3d-" && \
    ninja -C /build && mkdir -p /out && find /build -name "spirv*-mesa3d-.spv" -exec cp {} /out/ \; && \
    git -C /src log -1 --format="mesa-libclc ${LIBCLC_REF} %H" > /out/VERSION && ls /out

FROM base AS build-mesa
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential meson ninja-build pkg-config python3-mako python3-yaml python3-packaging python3-ply \
        python3-pycparser bison flex glslang-tools libwayland-bin wayland-protocols \
        libdrm-dev libexpat1-dev zlib1g-dev libzstd-dev libwayland-dev libwayland-egl-backend-dev libglvnd-dev \
        libelf-dev libudev-dev rustc bindgen llvm-22-dev libclang-22-dev libclang-cpp22-dev \
        libllvmspirvlib-22-dev libclc-22-dev spirv-tools spirv-tools-dev spirv-headers && \
    rm -rf /var/lib/apt/lists/*
COPY --from=mesa-src /src /src
RUN cd /src && meson setup /build --prefix=/opt/mesa --libdir=lib \
        -Dbuildtype=release -Dgallium-drivers=etnaviv -Dvulkan-drivers= -Dteflon=true -Dopengl=true \
        -Dplatforms=wayland -Dglx=disabled -Degl=enabled -Dgbm=enabled -Dgles1=disabled -Dgles2=enabled \
        -Dglvnd=enabled -Dllvm=enabled -Dshared-llvm=enabled -Dgallium-rusticl=true -Dvideo-codecs= \
        -Dzstd=enabled && \
    ninja -C /build && DESTDIR=/out ninja -C /build install > /dev/null && \
    { cp /src/.commit /out/opt/mesa/MESA_COMMIT 2>/dev/null || true; }

FROM base AS build-gst
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential meson ninja-build pkg-config python3 flex bison \
        libglib2.0-dev libgudev-1.0-dev libjpeg62-turbo-dev libdrm-dev libglvnd-dev libegl-dev libgles-dev \
        libwayland-dev wayland-protocols libwayland-bin && \
    rm -rf /var/lib/apt/lists/*
COPY --from=build-mesa /out/opt/mesa /opt/mesa
COPY --from=gst-src /src /src
RUN cd /src && PKG_CONFIG_PATH=/opt/mesa/lib/pkgconfig meson setup /build --prefix=/opt/gst --libdir=lib \
        --buildtype=release --wrap-mode=nofallback -Dauto_features=disabled \
        -Dbase=enabled -Dgood=enabled -Dbad=enabled -Dugly=disabled -Dlibav=disabled -Ddevtools=disabled \
        -Dges=disabled -Drtsp_server=disabled -Dpython=disabled -Dintrospection=disabled -Dexamples=disabled \
        -Dtests=disabled -Ddoc=disabled -Dtools=enabled -Dorc=disabled -Dlibnice=disabled -Dtls=disabled \
        -Dgstreamer:tools=enabled -Dgstreamer:check=disabled -Dgstreamer:benchmarks=disabled \
        -Dgstreamer:coretracers=enabled \
        -Dgst-plugins-base:videotestsrc=enabled -Dgst-plugins-base:app=enabled \
        -Dgst-plugins-base:videoconvertscale=enabled -Dgst-plugins-base:typefind=enabled \
        -Dgst-plugins-base:playback=enabled -Dgst-plugins-base:rawparse=enabled -Dgst-plugins-base:videorate=enabled \
        -Dgst-plugins-base:gl=enabled -Dgst-plugins-base:gl_api=gles2 -Dgst-plugins-base:gl_platform=egl \
        -Dgst-plugins-base:gl_winsys=gbm,egl,wayland -Dgst-plugins-base:drm=enabled \
        -Dgst-plugins-good:matroska=enabled -Dgst-plugins-good:isomp4=enabled -Dgst-plugins-good:multifile=enabled \
        -Dgst-plugins-good:v4l2=enabled -Dgst-plugins-good:v4l2-gudev=enabled -Dgst-plugins-good:jpeg=enabled \
        -Dgst-plugins-good:rtp=enabled -Dgst-plugins-good:rtpmanager=enabled -Dgst-plugins-good:udp=enabled \
        -Dgst-plugins-bad:v4l2codecs=enabled -Dgst-plugins-bad:videoparsers=enabled \
        -Dgst-plugins-bad:debugutils=enabled -Dgst-plugins-bad:mpegtsmux=enabled -Dgst-plugins-bad:mpegtsdemux=enabled \
        -Dgst-plugins-bad:kms=enabled -Dgst-plugins-bad:wayland=enabled && \
    ninja -C /build && DESTDIR=/out ninja -C /build install > /dev/null && \
    { cp /src/.commit /out/opt/gst/GST_COMMIT 2>/dev/null || true; }

FROM base
RUN apt-get update && apt-get install -y --no-install-recommends \
        libllvm22 libclang-cpp22 libclang-common-22-dev libllvmspirvlib22.1 spirv-tools libdrm2 libexpat1 zlib1g libzstd1 \
        libwayland-client0 libwayland-server0 libwayland-cursor0 libwayland-egl1 libglvnd0 libegl1 libgles2 \
        libelf1t64 libudev1 ocl-icd-libopencl1 clinfo libglib2.0-0t64 libgudev-1.0-0 libjpeg62-turbo && \
    rm -rf /var/lib/apt/lists/*
COPY --from=build-mesa /out/opt/mesa /opt/mesa
COPY --from=build-gst /out/opt/gst /opt/gst
COPY --from=libclc /out/spirv-mesa3d-.spv /out/spirv64-mesa3d-.spv /usr/lib/clc/
COPY --from=libclc /out/VERSION /opt/mesa/LIBCLC_VERSION
# Compute (OpenGL ES 3.1 and OpenCL) is opt-in in this Mesa; rusticl only enables listed drivers.
ENV LD_LIBRARY_PATH=/opt/mesa/lib:/opt/gst/lib \
    __EGL_VENDOR_LIBRARY_DIRS=/opt/mesa/share/glvnd/egl_vendor.d \
    OCL_ICD_VENDORS=/opt/mesa/etc/OpenCL/vendors \
    ETNA_EXPERIMENTAL_COMPUTE=1 \
    RUSTICL_ENABLE=etnaviv \
    PATH=/opt/gst/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    GST_PLUGIN_SYSTEM_PATH=/opt/gst/lib/gstreamer-1.0 \
    GST_PLUGIN_SCANNER=/opt/gst/libexec/gstreamer-1.0/gst-plugin-scanner
# NPU (Teflon) settings of the evaluation: each is an opt-in in this Mesa. They make the six test models
# correct and faster than NXP's driver; unset one to compare.
ENV ETNA_V8_CACHE=ki ETNA_PW_RESHAPE=128 ETNA_AVGPOOL=1 ETNA_ML_CACHED=1 ETNA_SRAM_ACT=0x31000 \
    ETNA_CPU_TRANSPOSE=1 ETNA_CPU_RESHUFFLE=1 ETNA_ML_LIST_ONCE=1 ETNA_ML_CMD_CACHE=1 TEFLON_REUSE_CONTEXT=1 \
    ETNA_NO_LOGISTIC=1 ETNA_MAXPOOL=1 ETNA_PER_AXIS=1 ETNA_TILE_BIG_KB=100 ETNA_CPU_DETRANSPOSE=1 \
    ETNA_ML_THREADS=4 TEFLON_NO_EDGE_RESHAPE=1 ETNA_ODD_TILE=1 ETNA_PW_FIT=1
