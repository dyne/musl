# Build base libs available in the toolchain

# set externally to cross-compile for targets
PREFIX ?= /opt/dyne
ARCH ?= x86_64-linux-musl

# versions available on files.dyne.org
LIBSSL ?= libressl-4.1.0
ZLIB ?= zlib-ng-2.2.4
CURL ?= curl-8.15.0
SSH2 ?= libssh2-1.11.1
CCACHE ?= ccache-4.11.3
CMAKE ?= cmake-4.1.1

R  := $(shell dirname $(CURDIR))
T  := $(R)/dyne/$(ARCH)

GCC_BINS := $(R)/dyne/gcc-musl/bin/$(ARCH)
CC  := ccache $(GCC_BINS)-gcc --static
CXX := ccache $(GCC_BINS)-g++ --static
ASM := $(GCC_BINS)-as
AR := $(GCC_BINS)-ar

all: \
	$(T)/lib/libssl.a  \
	$(T)/lib/libz.a    \
	$(T)/lib/libcurl.a \
	$(T)/lib/libssh2.a \
	$(T)/bin/ccache \
	$(T)/bin/cmake

$(T)/lib/libssl.a: $(LIBSSL).orig
	$(info Building SSL library)
	cd $(LIBSSL).orig \
	&& CC="$(CC)" AR="$(AR)" \
	CFLAGS="-static -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow" \
	./configure --prefix=$(T) --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --disable-tests --disable-dependency-tracking \
	&& $(MAKE) -j`nproc` && $(MAKE) install

$(T)/lib/libz.a: $(ZLIB).orig
	$(info Building Z library)
	mkdir -p $(ZLIB).orig/build && cd $(ZLIB).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} -DROOT="$(R)" \
	-DCMAKE_TOOLCHAIN_FILE="${R}/settings.cmake" -DCMAKE_INSTALL_PREFIX="${R}/dyne/${ARCH}" \
		-DZLIB_ENABLE_TESTS=0 -DZLIB_COMPAT=1 -DZLIBNG_ENABLE_TESTS=0 \
		-DWITH_SANITIZER=0 -DWITH_GTEST=0 -DBUILD_SHARED_LIBS=0 \
	&& ninja -C build && ninja -C build install

$(T)/lib/libcurl.a: $(CURL).orig
	$(info Building CURL library)
	mkdir -p $(CURL).orig/build && cd $(CURL).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} -DROOT="$(R)" \
	-DCMAKE_TOOLCHAIN_FILE="${R}/settings.cmake" -DCMAKE_INSTALL_PREFIX="${R}/dyne/${ARCH}" \
		-DBUILD_SHARED_LIBS=0 -DBUILD_STATIC_LIBS=1 -DBUILD_STATIC_CURL=1 \
		-DCURL_LTO=0 -DENABLE_THREADED_RESOLVER=1 -DCURL_USE_LIBPSL=0 \
	  -DBUILD_LIBCURL_DOCS=0 -DBUILD_MISC_DOCS=0 -DENABLE_CURL_MANUAL=0 \
		-DCURL_USE_OPENSSL=1 \
	&& ninja -C build && ninja -C build install

$(T)/lib/libssh2.a: $(SSH2).orig
	$(info Building SSH2 library)
	mkdir -p $(SSH2).orig/build && cd $(SSH2).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} -DROOT="$(R)" \
	-DCMAKE_TOOLCHAIN_FILE="${R}/settings.cmake" -DCMAKE_INSTALL_PREFIX="${R}/dyne/${ARCH}" \
		-DBUILD_SHARED_LIBS=0 -DBUILD_TESTING=0 -DBUILD_EXAMPLES=0 \
		-DCRYPTO_BACKEND="OpenSSL" \
	&& ninja -C build && ninja -C build install

# && CC="$(CC)" AR=$(AR) CFLAGS="-static -g0 -Os" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
# ./configure --prefix=$(PREFIX)/$(ARCH) --disable-shared --disable-tests --with-crypto=openssl --with-sysroot=$(PREFIX)  \
# --build=x86_64-linux-musl --host=$(ARCH) \
# && $(MAKE) -j`nproc` && $(MAKE) install

# -DCMAKE_INSTALL_PREFIX="${PREFIX}/${ARCH}"
$(T)/bin/ccache: $(CCACHE).orig
	$(info Building CCACHE)
	mkdir -p $(CCACHE).orig/build && cd $(CCACHE).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} -DROOT="$(R)" \
	-DCMAKE_TOOLCHAIN_FILE="${R}/settings.cmake" -DCMAKE_INSTALL_PREFIX="${R}/dyne/${ARCH}" \
		-DFORCE_STATIC=1 \
		-DHTTP_STORAGE_BACKEND=OFF -DENABLE_TESTING=OFF \
		-DREDIS_STORAGE_BACKEND=OFF -DSTATIC_LINK=ON \
	&& ninja -C build && ninja -C build install

$(T)/bin/cmake: $(CMAKE).orig
	$(info Building CMAKE)
	mkdir -p $(CMAKE).orig/build && cd $(CMAKE).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} -DROOT="$(R)" \
	-DCMAKE_TOOLCHAIN_FILE="${R}/settings.cmake" -DCMAKE_INSTALL_PREFIX="${R}/dyne/${ARCH}" \
		-DFORCE_STATIC=1 -DSTATIC_LINK=ON \
		-DBUILD_TESTING=OFF -DBUILD_CMAKE_DOCS=OFF \
	&& ninja -C build && ninja -C build install


# upstream: https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/
$(LIBSSL).tar.gz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

# upstream: https://github.com/zlib-ng/zlib-ng/releases
$(ZLIB).tar.gz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

# upstream: https://curl.se/download/curl-8.15.0.tar.xz
$(CURL).tar.xz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

# upstream: https://libssh2.org
$(SSH2).tar.xz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

$(CCACHE).tar.xz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

# upstream: https://github.com/Kitware/CMake/releases/download/v4.1.1/cmake-4.1.1.tar.gz
$(CMAKE).tar.gz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

clean:
	rm -rf *.orig
	rm -f \
		$(T)/lib/libssl.*    \
		$(T)/lib/libcrypto.* \
		$(T)/lib/libz.*    \
		$(T)/lib/libcurl.* \
		$(T)/lib/libssh2.* \
		$(T)/bin/ccache \
		$(T)/bin/cmake

%.orig: %.tar.gz
	tar zxf - < $<
	mv $(patsubst %.orig,%,$@) $@

%.orig: %.tar.xz
	tar Jxf - < $<
	mv $(patsubst %.orig,%,$@) $@
