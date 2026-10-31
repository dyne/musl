
SOURCES = sources

CONFIG_SUB_REV = 3d5db9ebe860
BINUTILS_VER = 2.47
GCC_VER = 16.2.0
MUSL_VER = 1.2.6
GMP_VER = 6.3.0
MPC_VER = 1.4.1
MPFR_VER = 4.2.2
LINUX_VER = 7.3.1

MUSL_REPO = https://git.musl-libc.org/git/musl

SOURCE_URLS ?= $(abspath ../sources.urls)
CHECKSUMS ?= $(abspath ../sources.sha256)
DOWNLOAD = sh $(abspath ../scripts/download.sh)

COWPATCH = $(CURDIR)/cowpatch.sh

HOST = $(if $(NATIVE),$(TARGET))
BUILD_DIR = build/$(if $(HOST),$(HOST),local)/$(TARGET)
OUTPUT = $(CURDIR)/output$(if $(HOST),-$(HOST))

REL_TOP = ../../..

-include config.mak

# ARCH is this wrapper's target tuple. Let leaf projects' own Makefiles set
# their ARCH (musl needs x86_64, not x86_64-linux-musl). Keep it as an environment
# default for this wrapper's config while demoting the command-line override.
MAKEOVERRIDES := $(filter-out ARCH=%,$(MAKEOVERRIDES))

SRC_DIRS = gcc-$(GCC_VER) binutils-$(BINUTILS_VER) musl-$(MUSL_VER) \
	$(if $(GMP_VER),gmp-$(GMP_VER)) \
	$(if $(MPC_VER),mpc-$(MPC_VER)) \
	$(if $(MPFR_VER),mpfr-$(MPFR_VER)) \
	$(if $(ISL_VER),isl-$(ISL_VER)) \
	$(if $(LINUX_VER),linux-$(LINUX_VER))

.PHONY: all install fetch-sources print-config clean distclean
all: fetch-sources

ARCHIVES = $(foreach dir,$(filter-out musl-git-%,$(SRC_DIRS)),$(notdir $(patsubst %.sha1,%,$(wildcard hashes/$(dir).tar.*.sha1))))
fetch-sources:
	@set -e; for archive in $(ARCHIVES); do \
		if [ "$(SOURCES)" != sources ] && [ ! -f "$(SOURCES)/$$archive" ]; then \
			echo "Missing archive in immutable SOURCES: $$archive" >&2; exit 1; \
		fi; \
		$(DOWNLOAD) "" "$(SOURCES)/$$archive" "$(CHECKSUMS)" "$$archive" "$(SOURCE_URLS)"; \
	done
	@test "$(SOURCES)" = sources || test -f "$(SOURCES)/config.sub"
	$(DOWNLOAD) "" "$(SOURCES)/config.sub" "$(CHECKSUMS)" "config.sub.$(CONFIG_SUB_REV)" "$(SOURCE_URLS)"

print-config:
	@$(foreach key,ARCH TARGET HOST GCC_VER BINUTILS_VER MUSL_VER LINUX_VER GMP_VER MPC_VER MPFR_VER ISL_VER CONFIG_SUB_REV COMMON_CONFIG GCC_CONFIG MUSL_CONFIG BINUTILS_CONFIG TOOLCHAIN_CONFIG,printf '%s\n' '$(key)=$($(key))';)

clean:
	rm -rf gcc-* binutils-* musl-* gmp-* mpc-* mpfr-* isl-* build build-* linux-*

distclean: clean
	rm -f sources/config.sub sources/*.tar.*


# Rules for downloading and verifying sources. Treat an external SOURCES path as
# immutable and do not try to download anything into it.

ifeq ($(SOURCES),sources)

$(SOURCES):
	mkdir -p $@

$(SOURCES)/config.sub: | $(SOURCES)
	$(DOWNLOAD) "" "$@" "$(CHECKSUMS)" "config.sub.$(CONFIG_SUB_REV)" "$(SOURCE_URLS)"

$(SOURCES)/%: hashes/%.sha1 | $(SOURCES)
	$(DOWNLOAD) "" "$@" "$(CHECKSUMS)" "$(notdir $@)" "$(SOURCE_URLS)"

endif


# Rules for extracting and patching sources, or checking them out from git.

musl-git-%:
	rm -rf $@.tmp
	git clone -b $(patsubst musl-git-%,%,$@) $(MUSL_REPO) $@.tmp
	cd $@.tmp && git fsck
	mv $@.tmp $@

%.orig: $(SOURCES)/%.tar.gz
	case "$@" in */*) exit 1 ;; esac
	rm -rf $@.tmp
	mkdir $@.tmp
	( cd $@.tmp && tar zxf - ) < $<
	rm -rf $@
	touch $@.tmp/$(patsubst %.orig,%,$@)
	mv $@.tmp/$(patsubst %.orig,%,$@) $@
	rm -rf $@.tmp

%.orig: $(SOURCES)/%.tar.bz2
	case "$@" in */*) exit 1 ;; esac
	rm -rf $@.tmp
	mkdir $@.tmp
	( cd $@.tmp && tar jxf - ) < $<
	rm -rf $@
	touch $@.tmp/$(patsubst %.orig,%,$@)
	mv $@.tmp/$(patsubst %.orig,%,$@) $@
	rm -rf $@.tmp

%.orig: $(SOURCES)/%.tar.xz
	case "$@" in */*) exit 1 ;; esac
	rm -rf $@.tmp
	mkdir $@.tmp
	( cd $@.tmp && tar Jxf - ) < $<
	rm -rf $@
	touch $@.tmp/$(patsubst %.orig,%,$@)
	mv $@.tmp/$(patsubst %.orig,%,$@) $@
	rm -rf $@.tmp

%: %.orig | $(SOURCES)/config.sub
	case "$@" in */*) exit 1 ;; esac
	rm -rf $@.tmp
	mkdir $@.tmp
	( cd $@.tmp && $(COWPATCH) -I ../$< )
	test ! -d patches/$@ || cat patches/$@/* | ( cd $@.tmp && $(COWPATCH) -p1 )
	if test -f $</configfsf.sub ; then cs=configfsf.sub ; elif test -f $</config.sub ; then cs=config.sub ; else exit 0 ; fi ; rm -f $@.tmp/$$cs && cp -f $(SOURCES)/config.sub $@.tmp/$$cs && chmod +x $@.tmp/$$cs
	rm -rf $@
	mv $@.tmp $@


# Add deps for all patched source dirs on their patchsets
$(foreach dir,$(notdir $(basename $(basename $(basename $(wildcard hashes/*))))),$(eval $(dir): $$(wildcard patches/$(dir) patches/$(dir)/*)))

extract_all: fetch-sources
	$(MAKE) extract-toolchain-sources

extract-toolchain-sources: | $(SRC_DIRS)


# Rules for building.

ifeq ($(TARGET),)

all:
	@echo TARGET must be set via config.mak or command line.
	@exit 1

else

$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/Makefile: | $(BUILD_DIR)
	ln -sf $(REL_TOP)/litecross/Makefile $@

$(BUILD_DIR)/config.mak: | $(BUILD_DIR)
	printf >$@ '%s\n' \
	"TARGET = $(TARGET)" \
	"HOST = $(HOST)" \
	"MUSL_SRCDIR = $(REL_TOP)/musl-$(MUSL_VER)" \
	"GCC_SRCDIR = $(REL_TOP)/gcc-$(GCC_VER)" \
	"BINUTILS_SRCDIR = $(REL_TOP)/binutils-$(BINUTILS_VER)" \
	$(if $(GMP_VER),"GMP_SRCDIR = $(REL_TOP)/gmp-$(GMP_VER)") \
	$(if $(MPC_VER),"MPC_SRCDIR = $(REL_TOP)/mpc-$(MPC_VER)") \
	$(if $(MPFR_VER),"MPFR_SRCDIR = $(REL_TOP)/mpfr-$(MPFR_VER)") \
	$(if $(ISL_VER),"ISL_SRCDIR = $(REL_TOP)/isl-$(ISL_VER)") \
	$(if $(LINUX_VER),"LINUX_SRCDIR = $(REL_TOP)/linux-$(LINUX_VER)") \
	"-include $(REL_TOP)/config.mak"

all:
	$(MAKE) build-toolchain

build-toolchain: | $(SRC_DIRS) $(BUILD_DIR) $(BUILD_DIR)/Makefile $(BUILD_DIR)/config.mak
	cd $(BUILD_DIR) && $(MAKE) all

install: all
	cd $(BUILD_DIR) && $(MAKE) OUTPUT=$(OUTPUT) install

endif

.SECONDARY:
