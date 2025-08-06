ARCH ?= x86_64-linux-musl

all: gcc libs
	$(info Build completed!)
	$(MAKE) prepare

chroot: /alpine/enter-chroot

gcc: dyne/gcc-musl/bin/$(ARCH)-gcc
libs: dyne/$(ARCH)/lib/libssl.a
prepare:
	sh prepare.sh $(ARCH)

/alpine/enter-chroot:
	./alpine-chroot-install -a x86_64 -d /alpine \
		-p "bash make cmake gcc build-base curl patch gawk ccache perl rsync xz samurai coreutils-fmt"

dyne/gcc-musl/bin/$(ARCH)-gcc:
	cd gcc-musl/sources && bash download_from_dyne.sh
	$(MAKE) -C gcc-musl -j`nproc`
	$(MAKE) -C gcc-musl install PREFIX=$(CURDIR)/dyne/gcc-musl

dyne/$(ARCH)/lib/libssl.a:
	$(MAKE) -C libs         ARCH=$(ARCH) PREFIX=$(CURDIR)/dyne/$(ARCH)


clean:
	rm -rf dyne
	$(MAKE) -C gcc-musl clean
	$(MAKE) -C libs clean
