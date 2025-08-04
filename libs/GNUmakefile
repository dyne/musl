# Build base libs available in the toolchain

# set externally to cross-compile for targets
PREFIX ?= /opt/musl-dyne
ARCH ?= x86_64-linux-musl

# versions available on files.dyne.org
LIBSSL ?= libressl-4.1.0
ZLIB ?= zlib-ng-2.2.4
CURL ?= curl-8.15.0
SSH2 ?= libssh2-1.11.1

# .PHONY: build-SSH2 build-CURL build-ZLIB build-LIBSSL

CC := ccache $(PREFIX)/bin/$(ARCH)-gcc
AR := $(PREFIX)/bin/$(ARCH)-ar
T  := $(PREFIX)/$(ARCH)

all: \
	$(T)/lib/libssl.a  \
	$(T)/lib/libz.a    \
	$(T)/lib/libcurl.a \
	$(T)/lib/libssh2.a

$(T)/lib/libssl.a: $(LIBSSL).orig
	$(info Building SSL library)
	cd $(LIBSSL).orig \
		&& CC="$(CC)" AR=$(AR) CFLAGS="-static -g0 -Os" \
			 ./configure --prefix=$(PREFIX)/$(ARCH) --disable-shared --disable-tests --disable-dependency-tracking --build=x86_64-linux-musl --host=$(ARCH) \
		&& $(MAKE) -j`nproc` && $(MAKE) install

$(T)/lib/libz.a: $(ZLIB).orig
	$(info Building Z library)
	mkdir -p $(ZLIB).orig/build && cd $(ZLIB).orig/build \
		&& CC=$(PREFIX)/bin/$(ARCH)-gcc AR=$(AR) CFLAGS="-static -g0 -Os" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 cmake .. -DZLIB_ENABLE_TESTS=no -DZLIB_COMPAT=yes \
								-DCMAKE_C_COMPILER=$(PREFIX)/bin/$(ARCH)-gcc -DCMAKE_C_COMPILER_LAUNCHER=ccache \
			 					-DCMAKE_PREFIX_PATH=$(PREFIX)/$(ARCH) -DCMAKE_INSTALL_PREFIX=$(PREFIX)/$(ARCH) \
							  -DZLIBNG_ENABLE_TESTS=no -DWITH_SANITIZER=no -DWITH_GTEST=no \
		&& $(MAKE) -j`nproc` && $(MAKE) install

$(T)/lib/libcurl.a: $(CURL).orig
	$(info Building CURL library)
	cd $(CURL).orig \
		&& CC="$(CC)" AR=$(AR) CFLAGS="-static -g0 -Os" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 ./configure --prefix=$(PREFIX)/$(ARCH) --disable-shared --with-zlib=$(PREFIX)/$(ARCH) --with-openssl --build=x86_64-linux-musl --host=$(ARCH) --with-sysroot=$(PREFIX)/$(ARCH) --without-libpsl --disable-docs \
		&& $(MAKE) -j`nproc` && $(MAKE) install

$(T)/lib/libssh2.a: $(SSH2).orig
	$(info Building SSH2 library)
	cd $(SSH2).orig \
		&& CC="$(CC)" AR=$(AR) CFLAGS="-static -g0 -Os" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 ./configure --prefix=$(PREFIX)/$(ARCH) --disable-shared --disable-tests --with-crypto=openssl --with-sysroot=$(PREFIX)  \
					--build=x86_64-linux-musl --host=$(ARCH) \
		&& $(MAKE) -j`nproc` && $(MAKE) install

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

clean:
	rm -rf *.orig
	rm -f \
		$(T)/lib/libssl.a  \
		$(T)/lib/libz.a    \
		$(T)/lib/libcurl.a \
		$(T)/lib/libssh2.a

%.orig: %.tar.gz
	tar zxf - < $<
	mv $(patsubst %.orig,%,$@) $@

%.orig: %.tar.xz
	tar Jxf - < $<
	mv $(patsubst %.orig,%,$@) $@
