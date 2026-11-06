require recipes-kernel/linux/linux-toradex-upstream.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/linux-toradex-upstream-7.3:"

LINUX_REPO = "git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"

# The preamble and SPI patches carried for 6.18 are all upstream in 7.3.
TDX_PATCHES = " \
    file://0001-thermal-imx-Update-critical-temp-threshold.patch \
    file://iptables-legacy.cfg \
"

# VeriSilicon VC8000E H.264 stateless encoder: Paul Kocialkowski's series v1 (lore
# 20260522101653.2565125-1-paulk@sys-base.io) rebased on 7.3.1, a Makefile fix-up for the
# rebase, and the overdrive clock rate for the encoder (500 MHz, as in the NXP BSP).
TDX_PATCHES += " \
    file://vc8000e/0001-media-h264-Add-a-more-generic-reflist-builder-init.patch \
    file://vc8000e/0002-media-uapi-Add-H.264-stateless-encode-support.patch \
    file://vc8000e/0003-media-h264-Add-SPS-video-definitions.patch \
    file://vc8000e/0004-media-h264-Add-stateless-encode-core.patch \
    file://vc8000e/0005-media-h264-Add-stateless-encode-rbsp.patch \
    file://vc8000e/0006-media-h264-Add-stateless-encode-reference-management.patch \
    file://vc8000e/0007-media-h264-Add-stateless-encode-rate-control.patch \
    file://vc8000e/0008-media-verisilicon-Report-default-pixel-coding-for-no.patch \
    file://vc8000e/0009-media-verisilicon-Cancel-job-with-runtime-pm-put-clk.patch \
    file://vc8000e/0010-media-hantro-use-hantro_decoded_buffer-only-for-dst_.patch \
    file://vc8000e/0011-media-verisilicon-Add-common-encoder-parm-and-framei.patch \
    file://vc8000e/0012-media-verisilicon-Add-support-for-the-VC8000E-H.264-.patch \
    file://vc8000e/0013-media-verilisicon-imx8m-Add-support-for-the-VC8000E-.patch \
    file://vc8000e/0014-arm64-dts-imx8mp-add-VC8000E-encoder-node.patch \
    file://vc8000e/0015-local-fix-v4l2-core-Makefile-after-applying-the-seri.patch \
    file://vc8000e/0016-arm64-dts-imx8mp-Run-the-VC8000E-at-the-overdrive-rate.patch \
"

PV = "7.3"
LINUX_VERSION ?= "7.3.1"
KBRANCH = "linux-7.3.y"
SRCREV_machine = "79a907609d53d5cd645b42c11550d295d43abf99"
