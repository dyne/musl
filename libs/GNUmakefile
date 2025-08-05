# Build base libs available in the toolchain

# set externally to cross-compile for targets
PREFIX ?= /opt/musl-dyne
ARCH ?= x86_64-linux-musl

# versions available on files.dyne.org
LIBSSL ?= libressl-4.1.0
ZLIB ?= zlib-ng-2.2.4
CURL ?= curl-8.15.0
SSH2 ?= libssh2-1.11.1
CCACHE ?= ccache-4.11.3


CC := ccache $(PREFIX)/bin/$(ARCH)-gcc
AR := $(PREFIX)/bin/$(ARCH)-ar
T  := $(PREFIX)/$(ARCH)
R  := $(shell dirname $(CURDIR))

all: \
	$(T)/lib/libssl.a  \
	$(T)/lib/libz.a    \
	$(T)/lib/libcurl.a \
	$(T)/lib/libssh2.a \
	$(T)/bin/ccache

$(T)/lib/libssl.a: $(LIBSSL).orig
	$(info Building SSL library)
	mkdir -p $(LIBSSL).orig/build && cd $(LIBSSL).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} \
	-DCMAKE_TOOLCHAIN_FILE=${R}/settings.cmake -DFOR_MUSL_DYNE=1 \
		-DLIBRESSL_TESTS=0 -DENABLE_NC=1 \
	&& ninja -C build && ninja -C build install

$(T)/lib/libz.a: $(ZLIB).orig
	$(info Building Z library)
	mkdir -p $(ZLIB).orig/build && cd $(ZLIB).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} \
	-DCMAKE_TOOLCHAIN_FILE=${R}/settings.cmake -DFOR_MUSL_DYNE=1 \
		-DZLIB_ENABLE_TESTS=0 -DZLIB_COMPAT=1 -DZLIBNG_ENABLE_TESTS=0 \
		-DWITH_SANITIZER=0 -DWITH_GTEST=0 -DBUILD_SHARED_LIBS=0 \
	&& ninja -C build && ninja -C build install

$(T)/lib/libcurl.a: $(CURL).orig
	$(info Building CURL library)
	mkdir -p $(CURL).orig/build && cd $(CURL).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} \
	-DCMAKE_TOOLCHAIN_FILE=${R}/settings.cmake -DFOR_MUSL_DYNE=1 \
		-DBUILD_SHARED_LIBS=0 -DBUILD_STATIC_LIBS=1 -DBUILD_STATIC_CURL=1 \
		-DCURL_LTO=1 -DENABLE_THREADED_RESOLVER=1 -DCURL_USE_LIBPSL=0 \
	  -DBUILD_LIBCURL_DOCS=0 -DBUILD_MISC_DOCS=0 -DENABLE_CURL_MANUAL=0 \
		-DCURL_USE_OPENSSL=1 \
	&& ninja -C build && ninja -C build install

$(T)/lib/libssh2.a: $(SSH2).orig
	$(info Building SSH2 library)
	mkdir -p $(SSH2).orig/build && cd $(SSH2).orig && \
	cmake -G Ninja -S . -B build -DARCH=${ARCH} \
	-DCMAKE_TOOLCHAIN_FILE=${R}/settings.cmake -DFOR_MUSL_DYNE=1 \
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
	cmake -G Ninja -S . -B build -DARCH=${ARCH} \
  -DCMAKE_TOOLCHAIN_FILE=${R}/settings.cmake -DFOR_MUSL_DYNE=1 \
		-DFORCE_STATIC=1 \
		-DHTTP_STORAGE_BACKEND=OFF -DENABLE_TESTING=OFF \
		-DREDIS_STORAGE_BACKEND=OFF -DSTATIC_LINK=ON \
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

clean:
	rm -rf *.orig
	rm -f \
		$(T)/lib/libssl.*    \
		$(T)/lib/libcrypto.* \
		$(T)/lib/libz.*    \
		$(T)/lib/libcurl.* \
		$(T)/lib/libssh2.* \
		$(T)/bin/ccache

%.orig: %.tar.gz
	tar zxf - < $<
	mv $(patsubst %.orig,%,$@) $@

%.orig: %.tar.xz
	tar Jxf - < $<
	mv $(patsubst %.orig,%,$@) $@
