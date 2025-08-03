
PREFIX ?= /opt/musl-dyne
ARCH ?= x86_64-linux-musl
LIBSSL ?= libressl-4.1.0
ZLIB ?= zlib-ng-2.2.4
CURL ?= curl-8.15.0

all: CC=$(PREFIX)/bin/$(ARCH)-gcc
all: AR=$(PREFIX)/bin/$(ARCH)-ar
all: $(LIBSSL).orig $(ZLIB).orig $(CURL).orig
	cd $(LIBSSL).orig \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static" \
			 ./configure --prefix=$(PREFIX) --disable-shared --disable-tests --disable-dependency-tracking --build=x86_64-linux-musl --host=$(ARCH) \
		&& $(MAKE) -j`nproc`
	cd $(ZLIB).orig \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 ./configure --prefix=$(PREFIX) --zlib-compat --static \
		&& $(MAKE) -j`nproc`
	cd $(CURL).orig \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static" PKG_CONFIG_PATH=$(PREFIX)/lib/pkgconfig \
			 ./configure --prefix=$(PREFIX) --disable-shared --with-zlib=$(PREFIX) --with-openssl --build=x86_64-linux-musl --host=$(ARCH) --with-sysroot=$(PREFIX) --without-libpsl --disable-docs \
		&& $(MAKE) -j`nproc`

# upstream: https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/
$(LIBSSL).tar.gz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

# upstream: https://github.com/zlib-ng/zlib-ng/releases
$(ZLIB).tar.gz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

# upstream: https://curl.se/download/curl-8.15.0.tar.xz
$(CURL).tar.xz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

install: $(LIBSSL).orig $(ZLIB).orig $(CURL).orig
	cd $(LIBSSL).orig && $(MAKE) install-strip
	cd $(ZLIB).orig   && $(MAKE) install
	cd $(CURL).orig   && $(MAKE) install

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
