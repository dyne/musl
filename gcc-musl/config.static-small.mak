ARCH ?= x86_64-linux-musl
PREFIX ?= $(shell dirname $(CURDIR))/dyne/gcc-musl

TARGET = $(ARCH)
OUTPUT = $(PREFIX)
GCC_VER = 16.2.0
BINUTILS_VER = 2.47
LINUX_VER = 7.3.1
COMMON_CONFIG += CFLAGS="-g0 -Os -march=x86-64-v2"
COMMON_CONFIG += CXXFLAGS="-g0 -Os -march=x86-64-v2"
# -march=x86-64-v2 -march=haswell
COMMON_CONFIG += LDFLAGS="-s"
CCACHE_LAUNCHER ?= $(shell command -v ccache 2>/dev/null)
COMMON_CONFIG += CC="$(CCACHE_LAUNCHER) gcc -static --static"
COMMON_CONFIG += CXX="$(CCACHE_LAUNCHER) g++ -static --static"
COMMON_CONFIG += --disable-nls --disable-libmudflap --disable-libsanitizer --disable-lto
# --disable-libquadmath --disable-decimal-float --disable-libitm
# --disable-fixed-point --disable-lto
GCC_CONFIG += --enable-languages=c,c++
