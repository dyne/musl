ARCH ?= x86_64-linux-musl
BUILD_FLAVOR ?= static-small
# Compatibility with the old wrapper option. MUSL_CONFIG has a different
# meaning (configure arguments) inside musl-cross-make; do not leak the name.
ifneq ($(filter static-small shared-optim,$(MUSL_CONFIG)),)
BUILD_FLAVOR := $(MUSL_CONFIG)
override MUSL_CONFIG :=
MAKEOVERRIDES := $(filter-out MUSL_CONFIG=%,$(MAKEOVERRIDES))
endif
ALPINE_BRANCH ?= v3.24
JOBS ?= $(shell nproc)
export ARCH

.PHONY: all chroot gcc libs prepare smoke test clean
all: prepare

chroot: /alpine/enter-chroot
/alpine/enter-chroot:
	./alpine-chroot-install -a x86_64 -b $(ALPINE_BRANCH) -d /alpine \
		-k 'ARCH CI QEMU_EMULATOR TRAVIS_.* CCACHE_.*' \
		-p 'bash make cmake gcc build-base musl-dev curl git patch gawk ccache perl rsync xz samurai m4 pkgconf coreutils-fmt file binutils python3'

# Always enter sub-builds; their own state decides what needs rebuilding.
gcc:
	test -f "gcc-musl/config.$(BUILD_FLAVOR).mak"
	cd gcc-musl && ln -sf "config.$(BUILD_FLAVOR).mak" config.mak
	sh scripts/toolchain-state.sh $(ARCH)
	$(MAKE) -C gcc-musl -j$(JOBS) ARCH=$(ARCH)
	$(MAKE) -C gcc-musl install ARCH=$(ARCH) PREFIX=$(CURDIR)/dyne/gcc-musl

libs: gcc
	$(MAKE) -C libs ARCH=$(ARCH) PREFIX=$(CURDIR)/dyne/$(ARCH) JOBS=$(JOBS)

prepare: libs
	bash prepare.sh $(ARCH)

smoke:
	bash scripts/smoke.sh $(ARCH)

test:
	python3 -m unittest discover -s tests -v

clean:
	$(MAKE) -C libs clean ARCH=$(ARCH)
	$(MAKE) -C gcc-musl clean
	rm -rf dyne build
