ARCH ?= x86_64-linux-musl

# for a list of targets: ls gcc-musl/*.mak
# shared-optim
MUSL_CONFIG ?= static-small

all: gcc libs
	$(info Build completed!)
	$(MAKE) prepare

chroot: /alpine/enter-chroot

gcc: dyne/gcc-musl/bin/$(ARCH)-gcc

libs: dyne/$(ARCH)/lib/libssl.a
prepare:
	sh prepare.sh $(ARCH)

/alpine/enter-chroot: APKS := bash make cmake gcc build-base musl-dev curl patch gawk ccache perl rsync xz samurai coreutils-fmt
/alpine/enter-chroot:
	$(info 💪 Alpine chroot packages: $(APKS))
	./alpine-chroot-install -a x86_64 -d /alpine -p "$(APKS)"

dyne/gcc-musl/bin/$(ARCH)-gcc:
	$(info 💪 GCC-musl build config: $(MUSL_CONFIG))
	cd gcc-musl && ln -sf config.$(MUSL_CONFIG).mak config.mak
	$(MAKE) -C gcc-musl/sources
	$(MAKE) -C gcc-musl -j`nproc`
	$(MAKE) -C gcc-musl install PREFIX=$(CURDIR)/dyne/gcc-musl

dyne/$(ARCH)/lib/libssl.a:
	$(info 💪 Base libs arch: $(ARCH))
	$(MAKE) -C libs         ARCH=$(ARCH) PREFIX=$(CURDIR)/dyne/$(ARCH)

clean:
	rm -rf dyne
	$(MAKE) -C gcc-musl clean
	$(MAKE) -C libs clean
