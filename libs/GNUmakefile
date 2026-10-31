# Target-local source/build directories prevent cross-target cache contamination.
.DEFAULT_GOAL := all
R := $(abspath ..)
ARCH ?= x86_64-linux-musl
PREFIX ?= $(R)/dyne/$(ARCH)
T := $(abspath $(PREFIX))
BUILD_ROOT ?= $(R)/build/libs
B := $(BUILD_ROOT)/$(ARCH)
SOURCE_CACHE ?= $(R)/.cache/sources
SOURCE_URLS ?= $(R)/sources.urls
CHECKSUMS ?= $(R)/sources.sha256
TOOLCHAIN ?= $(R)/dyne/gcc-musl
ifneq ($(filter / $(R) $(R)/dyne $(abspath $(TOOLCHAIN)),$(T)),)
$(error PREFIX must be a dedicated target library directory)
endif
JOBS ?= $(shell nproc)
CCACHE_LAUNCHER ?= $(shell command -v ccache 2>/dev/null)
CC := $(CCACHE_LAUNCHER) $(TOOLCHAIN)/bin/$(ARCH)-gcc --static
CXX := $(CCACHE_LAUNCHER) $(TOOLCHAIN)/bin/$(ARCH)-g++ --static
AR := $(TOOLCHAIN)/bin/$(ARCH)-ar
RANLIB := $(TOOLCHAIN)/bin/$(ARCH)-ranlib
CFLAGS ?= -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow
CXXFLAGS ?= $(CFLAGS)
LDFLAGS ?= -static
export PKG_CONFIG_LIBDIR := $(T)/lib/pkgconfig
export PKG_CONFIG_PATH :=
export PKG_CONFIG_SYSROOT_DIR :=

LIBSSL ?= libressl-4.4.0
ZLIB ?= zlib-ng-2.3.3
CURL ?= curl-8.23.0
SSH2 ?= libssh2-1.11.1
CCACHE ?= ccache-4.14.2
NCURSES ?= ncurses-6.6
KYOTOCAB ?= kyotocabinet-1.2.80

PACKAGES := $(LIBSSL) $(ZLIB) $(CURL) $(SSH2) $(CCACHE) $(NCURSES) $(KYOTOCAB)
ARCHIVES := $(LIBSSL).tar.gz $(ZLIB).tar.gz $(CURL).tar.xz $(SSH2).tar.xz $(CCACHE).tar.xz $(NCURSES).tar.gz $(KYOTOCAB).tar.gz
OUTPUTS := $(T)/lib/libssl.a $(T)/lib/libcrypto.a $(T)/lib/libz.a \
	$(T)/lib/libcurl.a $(T)/lib/libssh2.a $(T)/lib/libncursesw.a \
	$(T)/lib/libkyotocabinet.a $(T)/bin/ccache
CACHE_ENV = sh "$(R)/scripts/compiler-cache.sh" "$(CCACHE_LAUNCHER)" "$(TOOLCHAIN)/bin/$(ARCH)-gcc"
AUTOCONF_ENV = $(CACHE_ENV) env CC="$(CC)" CXX="$(CXX)" AR="$(AR)" RANLIB="$(RANLIB)" \
	CFLAGS="$(CFLAGS)" CXXFLAGS="$(CXXFLAGS)" LDFLAGS="$(LDFLAGS)"
CMAKE_FLAGS = -G Ninja -DARCH=$(ARCH) -DROOT="$(R)" -DTARGET_PREFIX="$(T)" \
	-DCMAKE_TOOLCHAIN_FILE="$(R)/settings.cmake" -DTOOLCHAIN_PREFIX="$(TOOLCHAIN)" \
	-DCMAKE_INSTALL_PREFIX="$(T)" -DCMAKE_C_FLAGS="$(CFLAGS) -static" \
	-DCMAKE_CXX_FLAGS="$(CXXFLAGS) -static" -DFORCE_STATIC=ON \
	-DCCACHE=$(if $(CCACHE_LAUNCHER),ON,OFF)

.PHONY: all fetch build clean FORCE
# Verify every cached input before any extraction or compilation starts.
all: build
fetch: $(addprefix $(SOURCE_CACHE)/,$(ARCHIVES))
	@set -e; for archive in $(ARCHIVES); do \
		sh "$(R)/scripts/download.sh" "" "$(SOURCE_CACHE)/$$archive" "$(CHECKSUMS)" "$$archive" "$(SOURCE_URLS)"; \
	done
build: $(OUTPUTS)

$(B)/config: FORCE
	@mkdir -p "$(B)"
	@set -e; { $(foreach key,ARCH T TOOLCHAIN CC CXX AR RANLIB CFLAGS CXXFLAGS LDFLAGS PACKAGES CCACHE_LAUNCHER,printf '%s\n' '$(key)=$($(key))';) \
		sha256sum GNUmakefile "$(R)/settings.cmake" "$(CHECKSUMS)" "$(TOOLCHAIN)/bin/$(ARCH)-gcc"; \
		if test "$(TOOLCHAIN)" = "$(R)/dyne/gcc-musl" && test -f "$(R)/build/toolchain/$(ARCH)/config"; then \
			sha256sum "$(R)/build/toolchain/$(ARCH)/config"; \
		fi; \
	} > "$@.tmp"
	@if cmp -s "$@.tmp" "$@"; then rm -f "$@.tmp"; else \
		rm -rf "$(T)"; mv -f "$@.tmp" "$@"; \
	fi

# Re-extract on configuration/version changes; never reuse another target's CMake cache.
define extract
$(B)/$(1)/.extracted: $(SOURCE_CACHE)/$(2) $(B)/config | fetch
	rm -rf "$(B)/$(1)"
	mkdir -p "$(B)/$(1)"
	tar -xf "$$<" -C "$(B)/$(1)" --strip-components=1
	touch "$$@"
endef
$(foreach archive,$(ARCHIVES),$(eval $(call extract,$(firstword $(subst .tar., ,$(archive))),$(archive))))

# These explicit file targets allow direct builds after fetching sources.
$(addprefix $(SOURCE_CACHE)/,$(ARCHIVES)):
	sh "$(R)/scripts/download.sh" "" "$@" "$(CHECKSUMS)" "$(notdir $@)" "$(SOURCE_URLS)"

# GNU make grouped targets rebuild LibreSSL when either archive is missing.
$(T)/lib/libssl.a $(T)/lib/libcrypto.a &: $(B)/$(LIBSSL)/.extracted
	cd "$(B)/$(LIBSSL)" && $(AUTOCONF_ENV) ./configure --prefix="$(T)" \
		--build=x86_64-linux-musl --host=$(ARCH) --disable-shared --disable-tests --disable-dependency-tracking
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(LIBSSL)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(LIBSSL)" install

$(T)/lib/libz.a: $(B)/$(ZLIB)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(ZLIB)" -B "$(B)/$(ZLIB)/build" $(CMAKE_FLAGS) \
		-DZLIB_COMPAT=ON -DZLIB_ENABLE_TESTS=OFF -DZLIBNG_ENABLE_TESTS=OFF \
		-DWITH_SANITIZER=OFF -DWITH_GTEST=OFF -DBUILD_SHARED_LIBS=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(ZLIB)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(ZLIB)/build"

$(T)/lib/libssh2.a: $(B)/$(SSH2)/.extracted $(T)/lib/libssl.a $(T)/lib/libcrypto.a $(T)/lib/libz.a
	$(CACHE_ENV) cmake -S "$(B)/$(SSH2)" -B "$(B)/$(SSH2)/build" $(CMAKE_FLAGS) \
		-DBUILD_SHARED_LIBS=OFF -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DCRYPTO_BACKEND=OpenSSL
	$(CACHE_ENV) cmake --build "$(B)/$(SSH2)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(SSH2)/build"

$(T)/lib/libcurl.a: $(B)/$(CURL)/.extracted $(T)/lib/libssl.a $(T)/lib/libcrypto.a $(T)/lib/libz.a $(T)/lib/libssh2.a
	$(CACHE_ENV) cmake -S "$(B)/$(CURL)" -B "$(B)/$(CURL)/build" $(CMAKE_FLAGS) \
		-DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON -DBUILD_STATIC_CURL=ON \
		-DCURL_LTO=OFF -DENABLE_THREADED_RESOLVER=ON -DCURL_USE_LIBPSL=OFF \
		-DBUILD_LIBCURL_DOCS=OFF -DBUILD_MISC_DOCS=OFF -DENABLE_CURL_MANUAL=OFF \
		-DCURL_USE_OPENSSL=ON -DCURL_USE_LIBSSH2=ON -DCURL_BROTLI=OFF -DCURL_ZSTD=OFF \
		-DOPENSSL_USE_STATIC_LIBS=TRUE
	$(CACHE_ENV) cmake --build "$(B)/$(CURL)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(CURL)/build"

$(T)/lib/libncursesw.a: $(B)/$(NCURSES)/.extracted
	cd "$(B)/$(NCURSES)" && $(AUTOCONF_ENV) ./configure --prefix="$(T)" \
		--build=x86_64-linux-musl --host=$(ARCH) --enable-widec \
		--with-normal --without-shared --without-cxx-binding --without-ada \
		--without-debug --without-tests --without-progs --disable-db-install \
		--with-default-terminfo-dir=/usr/share/terminfo \
		--with-terminfo-dirs=/etc/terminfo:/lib/terminfo:/usr/share/terminfo
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(NCURSES)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(NCURSES)" install

$(T)/lib/libkyotocabinet.a: $(B)/$(KYOTOCAB)/.extracted
	cd "$(B)/$(KYOTOCAB)" && $(AUTOCONF_ENV) ./configure --prefix="$(T)" \
		--build=x86_64-linux-musl --host=$(ARCH) --enable-static --disable-shared --disable-zlib
	# Upstream adds -march=native and -O2: preserve the selected target flags.
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(KYOTOCAB)" -j$(JOBS) \
		CFLAGS="$(CFLAGS) -fPIC -fsigned-char" CXXFLAGS="$(CXXFLAGS) -fPIC -fsigned-char"
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(KYOTOCAB)" install \
		CFLAGS="$(CFLAGS) -fPIC -fsigned-char" CXXFLAGS="$(CXXFLAGS) -fPIC -fsigned-char"

$(T)/bin/ccache: $(B)/$(CCACHE)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(CCACHE)" -B "$(B)/$(CCACHE)/build" $(CMAKE_FLAGS) \
		-DHTTP_STORAGE_BACKEND=OFF -DENABLE_TESTING=OFF -DREDIS_STORAGE_BACKEND=OFF -DSTATIC_LINK=ON
	$(CACHE_ENV) cmake --build "$(B)/$(CCACHE)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(CCACHE)/build"

clean:
	rm -rf "$(B)" "$(T)"
