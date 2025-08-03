
ARCH ?= x86_64-linux-musl
LIBSSL ?= libressl-4.1.0

all: CC=/opt/musl-dyne/bin/$(ARCH)-gcc
all: AR=/opt/musl-dyne/bin/$(ARCH)-ar
all: $(LIBSSL).orig
	cd $(LIBSSL).orig \
		&& CC=$(CC) AR=$(AR) CFLAGS="-static" \
			 ./configure --prefix=/opt/musl-dyne --disable-shared --disable-tests --disable-dependency-tracking \
		&& $(MAKE) -j`nproc`

# upstream: https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/
$(LIBSSL).tar.gz:
	curl -L https://files.dyne.org/?file=musl/sources/$@ --output $@

install: $(LIBSSL).orig
	cd $(LIBSSL).orig && $(MAKE) install-strip

clean:
	cd $(LIBSSL).orig && $(MAKE) clean

%.orig: %.tar.gz
	tar zxf - < $<
	mv $(patsubst %.orig,%,$@) $@
