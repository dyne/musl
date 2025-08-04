
PREFIX ?= /opt/musl-dyne
ARCH ?= x86_64-linux-musl
LIBSSL ?= libressl-4.1.0
ZLIB ?= zlib-ng-2.2.4
CURL ?= curl-8.15.0

all: CC=$(PREFIX)/bin/$(ARCH)-gcc
all: AR=$(PREFIX)/bin/$(ARCH)-ar
all: $(LIBSSL).orig $(ZLIB).orig $(CURL).orig
	cd $(LIBSSL).orig \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static -g0 -Os" \
			 ./configure --prefix=$(PREFIX)/$(ARCH) --disable-shared --disable-tests --disable-dependency-tracking --build=x86_64-linux-musl --host=$(ARCH) \
		&& $(MAKE) -j`nproc` && $(MAKE) install
	mkdir -p $(ZLIB).orig/build && cd $(ZLIB).orig/build \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static -g0 -Os" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 cmake .. -DZLIB_ENABLE_TESTS=no -DZLIB_COMPAT=yes -DCMAKE_C_COMPILER=$(CC) -DCMAKE_PREFIX_PATH=$(PREFIX) -DCMAKE_INSTALL_PREFIX=$(PREFIX)/$(ARCH) ZLIBNG_ENABLE_TESTS=no WITH_SANITIZER=no WITH_GTEST=no \
		&& $(MAKE) -j`nproc` && $(MAKE) install
	cd $(CURL).orig \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static -g0 -Os" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 ./configure --prefix=$(PREFIX)/$(ARCH) --disable-shared --with-zlib=$(PREFIX) --with-openssl --build=x86_64-linux-musl --host=$(ARCH) --with-sysroot=$(PREFIX) --without-libpsl --disable-docs \
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

clean:
	cd $(LIBSSL).orig && $(MAKE) clean
	cd $(ZLIB).orig   && $(MAKE) clean
	cd $(CURL).orig   && $(MAKE) clean

%.orig: %.tar.gz
	tar zxf - < $<
	mv $(patsubst %.orig,%,$@) $@

%.orig: %.tar.xz
	tar Jxf - < $<
	mv $(patsubst %.orig,%,$@) $@
