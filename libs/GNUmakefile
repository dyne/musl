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
BOOST ?= boost-1.92.0
SQLITE ?= sqlite-autoconf-3540100
ZMQ ?= zeromq-4.3.5
GMP ?= gmp-6.3.0
NETTLE ?= nettle-3.10.2
GNUTLS ?= gnutls-3.8.13
SODIUM ?= libsodium-1.0.22
SDL ?= SDL3-3.4.18
SDLIMAGE ?= SDL3_image-3.4.8
SDLTTF ?= SDL3_ttf-3.2.2
FREETYPE ?= freetype-2.15.0
HARFBUZZ ?= harfbuzz-15.0.0
IMGUI ?= imgui-1.93.0
BOOST_VERSION := $(patsubst boost-%,%,$(BOOST))
ZMQ_PATCHES := $(sort $(wildcard patches/$(ZMQ)/*.patch))
HARFBUZZ_PATCHES := $(sort $(wildcard patches/$(HARFBUZZ)/*.patch))
LIBRARY_PATCHES := $(ZMQ_PATCHES) $(HARFBUZZ_PATCHES)
PACKAGE_CMAKE := $(sort $(wildcard cmake/*.cmake cmake/imgui/*))

PACKAGES := $(LIBSSL) $(ZLIB) $(CURL) $(SSH2) $(CCACHE) $(NCURSES) $(KYOTOCAB) $(BOOST) $(SQLITE) $(GMP) $(NETTLE) $(GNUTLS) $(SODIUM) $(ZMQ) $(SDL) $(SDLIMAGE) $(SDLTTF) $(FREETYPE) $(HARFBUZZ) $(IMGUI)
ARCHIVES := $(LIBSSL).tar.gz $(ZLIB).tar.gz $(CURL).tar.xz $(SSH2).tar.xz $(CCACHE).tar.xz $(NCURSES).tar.gz $(KYOTOCAB).tar.gz \
	$(BOOST).tar.xz $(SQLITE).tar.gz $(GMP).tar.xz $(NETTLE).tar.gz $(GNUTLS).tar.xz $(SODIUM).tar.gz $(ZMQ).tar.gz \
	$(SDL).tar.gz $(SDLIMAGE).tar.gz $(SDLTTF).tar.gz $(FREETYPE).tar.xz $(HARFBUZZ).tar.xz $(IMGUI).tar.gz
BOOST_OUTPUTS := $(T)/include/boost/version.hpp $(T)/include/boost/multi_index_container.hpp \
	$(T)/lib/cmake/Boost-$(BOOST_VERSION)/BoostConfig.cmake
SQLITE_OUTPUTS := $(T)/lib/libsqlite3.a $(T)/include/sqlite3.h $(T)/lib/pkgconfig/sqlite3.pc
ZMQ_OUTPUTS := $(T)/lib/libzmq.a $(T)/include/zmq.h $(T)/lib/cmake/ZeroMQ/ZeroMQConfig.cmake \
	$(T)/lib/pkgconfig/libzmq.pc
GMP_OUTPUTS := $(T)/lib/libgmp.a $(T)/include/gmp.h $(T)/lib/pkgconfig/gmp.pc
NETTLE_OUTPUTS := $(T)/lib/libnettle.a $(T)/lib/libhogweed.a $(T)/include/nettle/version.h \
	$(T)/lib/pkgconfig/nettle.pc $(T)/lib/pkgconfig/hogweed.pc
GNUTLS_OUTPUTS := $(T)/lib/libgnutls.a $(T)/include/gnutls/gnutls.h $(T)/lib/pkgconfig/gnutls.pc
SODIUM_OUTPUTS := $(T)/lib/libsodium.a $(T)/include/sodium.h $(T)/lib/pkgconfig/libsodium.pc
SDL_OUTPUTS := $(T)/lib/libSDL3.a $(T)/include/SDL3/SDL.h $(T)/lib/pkgconfig/sdl3.pc \
	$(T)/lib/cmake/SDL3/SDL3Config.cmake
SDLIMAGE_OUTPUTS := $(T)/lib/libSDL3_image.a $(T)/include/SDL3_image/SDL_image.h \
	$(T)/lib/pkgconfig/sdl3-image.pc $(T)/lib/cmake/SDL3_image/SDL3_imageConfig.cmake
SDLTTF_OUTPUTS := $(T)/lib/libSDL3_ttf.a $(T)/include/SDL3_ttf/SDL_ttf.h \
	$(T)/lib/pkgconfig/sdl3-ttf.pc $(T)/lib/cmake/SDL3_ttf/SDL3_ttfConfig.cmake
FREETYPE_OUTPUTS := $(T)/lib/libfreetype.a $(T)/include/freetype2/ft2build.h \
	$(T)/lib/pkgconfig/freetype2.pc
HARFBUZZ_OUTPUTS := $(T)/lib/libharfbuzz.a $(T)/include/harfbuzz/hb.h \
	$(T)/lib/pkgconfig/harfbuzz.pc $(T)/lib/cmake/harfbuzz/harfbuzzConfig.cmake \
	$(T)/lib/cmake/harfbuzz/harfbuzz-targets.cmake
IMGUI_OUTPUTS := $(T)/lib/libimgui.a $(T)/include/imgui/imgui.h \
	$(T)/include/imgui/backends/imgui_impl_sdl3.h $(T)/include/imgui/backends/imgui_impl_sdlrenderer3.h \
	$(T)/lib/pkgconfig/imgui.pc $(T)/lib/cmake/imgui/imguiConfig.cmake $(T)/lib/cmake/imgui/imguiTargets.cmake
OUTPUTS := $(T)/lib/libssl.a $(T)/lib/libcrypto.a $(T)/lib/libz.a \
	$(T)/lib/libcurl.a $(T)/lib/libssh2.a $(T)/lib/libncursesw.a \
	$(T)/lib/libkyotocabinet.a $(T)/bin/ccache $(BOOST_OUTPUTS) $(SQLITE_OUTPUTS) $(GMP_OUTPUTS) $(NETTLE_OUTPUTS) $(GNUTLS_OUTPUTS) $(SODIUM_OUTPUTS) $(ZMQ_OUTPUTS) \
	$(SDL_OUTPUTS) $(SDLIMAGE_OUTPUTS) $(SDLTTF_OUTPUTS) $(FREETYPE_OUTPUTS) $(HARFBUZZ_OUTPUTS) $(IMGUI_OUTPUTS)
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
		$(foreach input,$(LIBRARY_PATCHES) $(PACKAGE_CMAKE),sha256sum "$(input)";) \
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
		-DWITH_SANITIZER=OFF -DWITH_GTEST=OFF -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON
	$(CACHE_ENV) cmake --build "$(B)/$(ZLIB)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(ZLIB)/build"
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/zlib.pc"

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

# Upstream's Bitcoin-compatible header-only profile supplies relocatable CMake
# packages. Also install the complete header tree, without compiled Boost libs.
$(BOOST_OUTPUTS) &: $(B)/$(BOOST)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(BOOST)" -B "$(B)/$(BOOST)/build" $(CMAKE_FLAGS) \
		-DCMAKE_INSTALL_LIBDIR=lib -DBOOST_INCLUDE_LIBRARIES="multi_index;test" \
		-DBOOST_TEST_HEADERS_ONLY=ON -DBOOST_ENABLE_MPI=OFF -DBOOST_ENABLE_PYTHON=OFF \
		-DBOOST_INSTALL_LAYOUT=system -DBUILD_TESTING=OFF -DCMAKE_DISABLE_FIND_PACKAGE_ICU=ON
	$(CACHE_ENV) cmake --install "$(B)/$(BOOST)/build"
	@set -e; for headers in "$(B)/$(BOOST)"/libs/*/include "$(B)/$(BOOST)"/libs/numeric/*/include; do \
		if test -d "$$headers"; then cp -R "$$headers/." "$(T)/include/"; fi; \
	done
	mkdir -p "$(T)/share/licenses/boost"
	cp "$(B)/$(BOOST)/LICENSE_1_0.txt" "$(T)/share/licenses/boost/"

$(SQLITE_OUTPUTS) &: $(B)/$(SQLITE)/.extracted
	cd "$(B)/$(SQLITE)" && $(AUTOCONF_ENV) CC_FOR_BUILD=gcc \
		CFLAGS="$(CFLAGS) -fPIC -DSQLITE_DQS=0 -DSQLITE_DEFAULT_MEMSTATUS=0" \
		./configure --prefix="$(T)" --libdir="$(T)/lib" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --disable-readline --disable-load-extension
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(SQLITE)" -j$(JOBS) libsqlite3.a
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(SQLITE)" install-lib install-headers install-pc
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/sqlite3.pc"

# GCC's host GMP is separate: applications need an ARCH-targeted copy.
$(GMP_OUTPUTS) &: $(B)/$(GMP)/.extracted
	cd "$(B)/$(GMP)" && $(AUTOCONF_ENV) CFLAGS="$(CFLAGS) -std=gnu17" ./configure --prefix="$(T)" --libdir="$(T)/lib" \
		--build=x86_64-linux-musl --host=$(ARCH) --disable-shared --enable-static --with-pic
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(GMP)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(GMP)" install
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/gmp.pc"
	mkdir -p "$(T)/share/licenses/gmp"
	cp "$(B)/$(GMP)"/COPYING* "$(T)/share/licenses/gmp/"

# Nettle 3 is the supported API used by GnuTLS 3.8 (Nettle 4 changes it).
$(NETTLE_OUTPUTS) &: $(B)/$(NETTLE)/.extracted $(GMP_OUTPUTS)
	cd "$(B)/$(NETTLE)" && $(AUTOCONF_ENV) CPPFLAGS="-I$(T)/include" \
		LDFLAGS="$(LDFLAGS) -L$(T)/lib" ./configure --prefix="$(T)" --libdir="$(T)/lib" \
		--build=x86_64-linux-musl --host=$(ARCH) --disable-shared --enable-static --enable-pic --disable-documentation
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(NETTLE)" -j$(JOBS) libnettle.a libhogweed.a
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(NETTLE)" install-static install-headers install-pkgconfig
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/nettle.pc" "$(T)/lib/pkgconfig/hogweed.pc"
	mkdir -p "$(T)/share/licenses/nettle"
	cp "$(B)/$(NETTLE)"/COPYING* "$(T)/share/licenses/nettle/"

$(GNUTLS_OUTPUTS) &: $(B)/$(GNUTLS)/.extracted $(NETTLE_OUTPUTS) $(GMP_OUTPUTS) $(T)/lib/libz.a
	cd "$(B)/$(GNUTLS)" && $(AUTOCONF_ENV) CPPFLAGS="-I$(T)/include" \
		LDFLAGS="$(LDFLAGS) -L$(T)/lib" PKG_CONFIG="pkg-config --static" \
		./configure --prefix="$(T)" --libdir="$(T)/lib" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --enable-static --with-pic --disable-doc --disable-tools --disable-tests \
		--disable-cxx --disable-nls --disable-libdane --without-idn --without-p11-kit --without-tpm --without-tpm2 \
		--with-included-libtasn1 --with-included-unistring --with-zlib=link --without-brotli --without-zstd \
		--with-default-trust-store-file=/etc/ssl/certs/ca-certificates.crt
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(GNUTLS)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(GNUTLS)" install
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/gnutls.pc"
	mkdir -p "$(T)/share/licenses/gnutls"
	cp "$(B)/$(GNUTLS)"/COPYING* "$(T)/share/licenses/gnutls/"

$(SODIUM_OUTPUTS) &: $(B)/$(SODIUM)/.extracted
	cd "$(B)/$(SODIUM)" && $(AUTOCONF_ENV) CFLAGS="$(CFLAGS) -fPIC" \
		./configure --prefix="$(T)" --libdir="$(T)/lib" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --enable-static --with-pic
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(SODIUM)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(SODIUM)" install
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/libsodium.pc"
	mkdir -p "$(T)/share/licenses/libsodium"
	cp "$(B)/$(SODIUM)/LICENSE" "$(T)/share/licenses/libsodium/"

$(B)/$(ZMQ)/.patched: $(B)/$(ZMQ)/.extracted $(ZMQ_PATCHES)
	@set -e; for source_patch in $(ZMQ_PATCHES); do \
		patch --fuzz=0 -d "$(B)/$(ZMQ)" -p1 < "$$source_patch"; \
	done
	touch "$@"

$(ZMQ_OUTPUTS) &: $(B)/$(ZMQ)/.patched $(GNUTLS_OUTPUTS) $(SODIUM_OUTPUTS)
	$(CACHE_ENV) cmake -S "$(B)/$(ZMQ)" -B "$(B)/$(ZMQ)/build" $(CMAKE_FLAGS) \
		-DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
		-DBUILD_SHARED=OFF -DBUILD_STATIC=ON -DBUILD_TESTS=OFF -DZMQ_BUILD_TESTS=OFF \
		-DWITH_DOCS=OFF -DENABLE_CPACK=OFF -DENABLE_DRAFTS=ON -DENABLE_CURVE=ON \
		-DWITH_LIBSODIUM=ON -DWITH_LIBSODIUM_STATIC=ON -DWITH_LIBBSD=OFF -DWITH_OPENPGM=OFF -DWITH_NORM=OFF \
		-DENABLE_WS=ON -DWITH_TLS=ON -DWITH_NSS=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(ZMQ)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(ZMQ)/build"
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e 's|^exec_prefix=.*|exec_prefix=$${prefix}|' -e 's|^libdir=.*|libdir=$${prefix}/lib|' \
		-e 's|^includedir=.*|includedir=$${prefix}/include|' "$(T)/lib/pkgconfig/libzmq.pc"
	mkdir -p "$(T)/share/licenses/zeromq"
	cp "$(B)/$(ZMQ)/LICENSE" "$(T)/share/licenses/zeromq/"

# Headless profile: deterministic software rendering with no display/audio
# service dependencies and no runtime dlopen in fully static musl applications.
$(SDL_OUTPUTS) &: $(B)/$(SDL)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(SDL)" -B "$(B)/$(SDL)/build" $(CMAKE_FLAGS) \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
		-DSDL_SHARED=OFF -DSDL_STATIC=ON -DSDL_RELOCATABLE=ON -DSDL_DEPS_SHARED=OFF \
		-DSDL_TESTS=OFF -DSDL_TEST_LIBRARY=OFF -DSDL_EXAMPLES=OFF -DSDL_INSTALL_CPACK=OFF \
		-DSDL_UNIX_CONSOLE_BUILD=ON -DSDL_X11=OFF -DSDL_WAYLAND=OFF -DSDL_KMSDRM=OFF -DSDL_OPENGL=OFF -DSDL_OPENGLES=OFF \
		-DSDL_VULKAN=OFF -DSDL_GPU=OFF -DSDL_OFFSCREEN=ON -DSDL_DUMMYVIDEO=ON \
		-DSDL_ALSA=OFF -DSDL_JACK=OFF -DSDL_PIPEWIRE=OFF -DSDL_PULSEAUDIO=OFF -DSDL_SNDIO=OFF -DSDL_OSS=OFF \
		-DSDL_DBUS=OFF -DSDL_IBUS=OFF -DSDL_LIBUDEV=OFF -DSDL_LIBURING=OFF -DSDL_HIDAPI=OFF \
		-DSDL_CAMERA=OFF -DSDL_DIALOG=OFF -DSDL_LOADSO=OFF -DSDL_RPI=OFF -DSDL_ROCKCHIP=OFF -DSDL_VIVANTE=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(SDL)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(SDL)/build"
	mkdir -p "$(T)/share/licenses/SDL3"
	cp "$(B)/$(SDL)/LICENSE.txt" "$(T)/share/licenses/SDL3/"

$(SDLIMAGE_OUTPUTS) &: $(B)/$(SDLIMAGE)/.extracted $(SDL_OUTPUTS)
	$(CACHE_ENV) cmake -S "$(B)/$(SDLIMAGE)" -B "$(B)/$(SDLIMAGE)/build" $(CMAKE_FLAGS) \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF \
		-DSDLIMAGE_VENDORED=OFF -DSDLIMAGE_DEPS_SHARED=OFF -DSDLIMAGE_RELOCATABLE=ON \
		-DSDLIMAGE_BACKEND_STB=ON -DSDLIMAGE_PNG_LIBPNG=OFF -DSDLIMAGE_AVIF=OFF \
		-DSDLIMAGE_JXL=OFF -DSDLIMAGE_TIF=OFF -DSDLIMAGE_WEBP=OFF \
		-DSDLIMAGE_SAMPLES=OFF -DSDLIMAGE_TESTS=OFF -DSDLIMAGE_INSTALL_CPACK=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(SDLIMAGE)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(SDLIMAGE)/build"
	mkdir -p "$(T)/share/licenses/SDL3_image"
	cp "$(B)/$(SDLIMAGE)/LICENSE.txt" "$(T)/share/licenses/SDL3_image/"
	# Preserve notices belonging to the compiled-in image codecs.
	cp $(addprefix "$(B)/$(SDLIMAGE)/src/",stb_image.h nanosvg.h nanosvgrast.h) "$(T)/share/licenses/SDL3_image/"

# HarfBuzz uses FreeType's rasterizer; disable FreeType's reverse dependency to
# keep an acyclic static dependency graph. Reuse our target zlib for .gz fonts.
$(FREETYPE_OUTPUTS) &: $(B)/$(FREETYPE)/.extracted $(T)/lib/libz.a
	$(CACHE_ENV) cmake -S "$(B)/$(FREETYPE)" -B "$(B)/$(FREETYPE)/build" $(CMAKE_FLAGS) \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF \
		-DFT_REQUIRE_ZLIB=ON -DFT_DISABLE_BZIP2=ON -DFT_DISABLE_PNG=ON \
		-DFT_DISABLE_HARFBUZZ=ON -DFT_DISABLE_BROTLI=ON
	$(CACHE_ENV) cmake --build "$(B)/$(FREETYPE)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(FREETYPE)/build"
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' "$(T)/lib/pkgconfig/freetype2.pc"
	mkdir -p "$(T)/share/licenses/freetype"
	cp "$(B)/$(FREETYPE)/LICENSE.TXT" "$(B)/$(FREETYPE)/docs/FTL.TXT" "$(B)/$(FREETYPE)/docs/GPLv2.TXT" "$(T)/share/licenses/freetype/"

$(B)/$(HARFBUZZ)/.patched: $(B)/$(HARFBUZZ)/.extracted $(HARFBUZZ_PATCHES)
	@set -e; for source_patch in $(HARFBUZZ_PATCHES); do \
		patch --fuzz=0 -d "$(B)/$(HARFBUZZ)" -p1 < "$$source_patch"; \
	done
	touch "$@"

$(HARFBUZZ_OUTPUTS) &: $(B)/$(HARFBUZZ)/.patched $(FREETYPE_OUTPUTS)
	$(CACHE_ENV) cmake -S "$(B)/$(HARFBUZZ)" -B "$(B)/$(HARFBUZZ)/build" $(CMAKE_FLAGS) \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF \
		-DHB_HAVE_FREETYPE=ON -DHB_HAVE_CAIRO=OFF -DHB_HAVE_GLIB=OFF -DHB_HAVE_ICU=OFF -DHB_HAVE_GRAPHITE2=OFF \
		-DHB_BUILD_UTILS=OFF -DHB_BUILD_SUBSET=OFF -DHB_BUILD_RASTER=OFF -DHB_BUILD_VECTOR=OFF -DHB_BUILD_GPU=OFF \
		-DHB_BUILD_GPU_DEMO=OFF -DBUILD_TESTING=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(HARFBUZZ)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(HARFBUZZ)/build"
	mv "$(T)/lib/cmake/harfbuzz/harfbuzzConfig.cmake" "$(T)/lib/cmake/harfbuzz/harfbuzz-targets.cmake"
	cp cmake/harfbuzzConfig.cmake "$(T)/lib/cmake/harfbuzz/harfbuzzConfig.cmake"
	sed -i -e 's|^prefix=.*|prefix=$${pcfiledir}/../..|' \
		-e '/^Libs.private:/s/$$/ -lstdc++/' "$(T)/lib/pkgconfig/harfbuzz.pc"
	mkdir -p "$(T)/share/licenses/harfbuzz"
	cp "$(B)/$(HARFBUZZ)/COPYING" "$(T)/share/licenses/harfbuzz/"

$(SDLTTF_OUTPUTS) &: $(B)/$(SDLTTF)/.extracted $(SDL_OUTPUTS) $(FREETYPE_OUTPUTS) $(HARFBUZZ_OUTPUTS)
	$(CACHE_ENV) cmake -S "$(B)/$(SDLTTF)" -B "$(B)/$(SDLTTF)/build" $(CMAKE_FLAGS) \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF \
		-DSDLTTF_VENDORED=OFF -DSDLTTF_HARFBUZZ=ON -DSDLTTF_PLUTOSVG=OFF \
		-DSDLTTF_RELOCATABLE=ON -DSDLTTF_SAMPLES=OFF -DSDLTTF_INSTALL_CPACK=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(SDLTTF)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(SDLTTF)/build"
	mkdir -p "$(T)/share/licenses/SDL3_ttf"
	cp "$(B)/$(SDLTTF)/LICENSE.txt" "$(T)/share/licenses/SDL3_ttf/"

# Upstream intentionally ships source files rather than a CMake package.
# Bundle only the SDL3 platform/SDL_Renderer3 backends; fonts use bundled stb.
$(IMGUI_OUTPUTS) &: $(B)/$(IMGUI)/.extracted $(SDL_OUTPUTS)
	$(CACHE_ENV) cmake -S cmake/imgui -B "$(B)/$(IMGUI)/build" $(CMAKE_FLAGS) \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
		-DIMGUI_SOURCE_DIR="$(B)/$(IMGUI)" -DIMGUI_VERSION="$(patsubst imgui-%,%,$(IMGUI))"
	$(CACHE_ENV) cmake --build "$(B)/$(IMGUI)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(IMGUI)/build"

clean:
	rm -rf "$(B)" "$(T)"
