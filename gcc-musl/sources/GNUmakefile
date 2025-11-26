# We redistribute the sources to overcome flaky mirrors upload to
# files.dyne.org after downloading with upstream's makefile and then
# scp all contents of sources subdir

all: config.sub \
	binutils-2.44.tar.gz \
	gcc-15.1.0.tar.xz \
	gmp-6.1.2.tar.bz2 \
	linux-5.8.5.tar.xz \
	mpc-1.1.0.tar.gz \
	mpfr-4.0.2.tar.bz2 \
	musl-1.2.5.tar.gz

%.sub:
	curl -L https://files.dyne.org/sources/$@ --output $@

%.tar.gz:
	curl -L https://files.dyne.org/sources/$@ --output $@

%.tar.xz:
	curl -L https://files.dyne.org/sources/$@ --output $@

%.tar.bz2:
	curl -L https://files.dyne.org/sources/$@ --output $@

clean:
	rm -f *.sub *.tar.*
