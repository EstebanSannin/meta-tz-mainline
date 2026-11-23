require recipes-kernel/linux/linux-toradex-upstream.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/linux-toradex-upstream-7.3:"

LINUX_REPO = "git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"

# Stable 7.3.1 plus the tz-upstream/imx8mp kernel branch, exported with git format-patch:
# - the Toradex thermal patch (the other 6.18 patches are upstream in 7.3);
# - Paul Kocialkowski's VC8000E H.264 encoder series v1 and a Makefile fix-up for 7.3.1;
# - VC8000E at 500 MHz and the ISI enabled on Verdin;
# - etnaviv: a CPU latency request while the GPU/NPU is busy.
TDX_PATCHES = " \
    file://tz-upstream/0001-thermal-imx-Update-critical-temp-threshold.patch \
    file://tz-upstream/0002-media-h264-Add-a-more-generic-reflist-builder-init.patch \
    file://tz-upstream/0003-media-uapi-Add-H.264-stateless-encode-support.patch \
    file://tz-upstream/0004-media-h264-Add-SPS-video-definitions.patch \
    file://tz-upstream/0005-media-h264-Add-stateless-encode-core.patch \
    file://tz-upstream/0006-media-h264-Add-stateless-encode-rbsp.patch \
    file://tz-upstream/0007-media-h264-Add-stateless-encode-reference-management.patch \
    file://tz-upstream/0008-media-h264-Add-stateless-encode-rate-control.patch \
    file://tz-upstream/0009-media-verisilicon-Report-default-pixel-coding-for-no.patch \
    file://tz-upstream/0010-media-verisilicon-Cancel-job-with-runtime-pm-put-clk.patch \
    file://tz-upstream/0011-media-hantro-use-hantro_decoded_buffer-only-for-dst_.patch \
    file://tz-upstream/0012-media-verisilicon-Add-common-encoder-parm-and-framei.patch \
    file://tz-upstream/0013-media-verisilicon-Add-support-for-the-VC8000E-H.264-.patch \
    file://tz-upstream/0014-media-verilisicon-imx8m-Add-support-for-the-VC8000E-.patch \
    file://tz-upstream/0015-arm64-dts-imx8mp-add-VC8000E-encoder-node.patch \
    file://tz-upstream/0016-local-fix-v4l2-core-Makefile-after-the-VC8000E-serie.patch \
    file://tz-upstream/0017-arm64-dts-imx8mp-VC8000E-overdrive-rate-ISI-on-Verdi.patch \
    file://tz-upstream/0018-drm-etnaviv-hold-a-CPU-latency-request-while-the-GPU.patch \
    file://iptables-legacy.cfg \
"

PV = "7.3"
LINUX_VERSION ?= "7.3.1"
KBRANCH = "linux-7.3.y"
SRCREV_machine = "79a907609d53d5cd645b42c11550d295d43abf99"
