ARCH ?= x86_64-linux-musl

all: gcc libs strip

chroot: /alpine/enter-chroot

gcc: dyne/gcc-musl/bin/$(ARCH)-gcc
libs: dyne/$(ARCH)/lib/libssl.a

/alpine/enter-chroot:
	./alpine-chroot-install -a x86_64 -d /alpine \
		-p "bash make cmake gcc build-base curl patch gawk ccache perl rsync xz samurai coreutils-fmt"

dyne/gcc-musl/bin/$(ARCH)-gcc:
	cd gcc-musl/sources && bash download_from_dyne.sh
	$(MAKE) -C gcc-musl -j`nproc`
	$(MAKE) -C gcc-musl install PREFIX=$(CURDIR)/dyne/gcc-musl

dyne/$(ARCH)/lib/libssl.a:
	$(MAKE) -C libs         ARCH=$(ARCH) PREFIX=$(CURDIR)/dyne/$(ARCH)

strip:
	rm -f dyne/bin/*-lto-dump
	rm -rf dyne/share
	cat README.md | awk '{gsub(/\[[^][]+\]\([^()]+\)/, gensub(/\[([^][]+)\]\([^()]+\)/, "\\1", "g")); print}' | fmt -w 72 | tee dyne/$(ARCH)/README.txt > dyne/gcc-musl/README.txt
	cp settings.cmake dyne/gcc-musl

clean:
	rm -rf dyne
	$(MAKE) -C gcc-musl clean
	$(MAKE) -C libs clean
