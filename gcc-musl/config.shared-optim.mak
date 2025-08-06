ARCH ?= x86_64-linux-musl
PREFIX ?= $(shell dirname $(CURDIR))/dyne/gcc-musl

TARGET = $(ARCH)
OUTPUT = $(PREFIX)
GCC_VER = 15.1.0
BINUTILS_VER = 2.44
LINUX_VER = 5.8.5
COMMON_CONFIG += CFLAGS="-g0 -O3 -march=native"
COMMON_CONFIG += CXXFLAGS="-g0 -O3 -march=native"
# -march=x86-64-v2 -march=haswell
COMMON_CONFIG += LDFLAGS="-s"
COMMON_CONFIG += CC="ccache gcc"
COMMON_CONFIG += CXX="ccache g++"
COMMON_CONFIG += --disable-nls --disable-libmudflap --disable-libsanitizer
# --disable-libquadmath --disable-decimal-float --disable-libitm --disable-lto
# --disable-fixed-point --disable-lto
GCC_CONFIG += --enable-languages=c,c++
