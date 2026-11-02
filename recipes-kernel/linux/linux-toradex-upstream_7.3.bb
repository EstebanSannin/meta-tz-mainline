require recipes-kernel/linux/linux-toradex-upstream.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/linux-toradex-upstream-7.3:"

LINUX_REPO = "git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"

# The preamble and SPI patches carried for 6.18 are all upstream in 7.3.
TDX_PATCHES = " \
    file://0001-thermal-imx-Update-critical-temp-threshold.patch \
    file://iptables-legacy.cfg \
"

PV = "7.3"
LINUX_VERSION ?= "7.3.1"
KBRANCH = "linux-7.3.y"
SRCREV_machine = "79a907609d53d5cd645b42c11550d295d43abf99"
