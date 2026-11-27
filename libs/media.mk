PIXMAN ?= pixman-0.46.4
LIBPNG ?= libpng-1.6.59
LIBXML2 ?= libxml2-2.15.4
FONTCONFIG ?= fontconfig-2.18.4
FRIBIDI ?= fribidi-1.0.18
CAIRO ?= cairo-1.18.6
PANGO ?= pango-1.58.2
RSVG ?= librsvg-2.62.4
ALSA ?= alsa-lib-1.2.16.1

RUST_VERSION ?= 1.96.1
RUST_HOST ?= $(if $(shell getconf GNU_LIBC_VERSION 2>/dev/null),x86_64-unknown-linux-gnu,x86_64-unknown-linux-musl)
CARGO_C ?= cargo-c-0.10.28-x86_64-unknown-linux-musl
CARGO_HOME ?= $(R)/.cache/cargo
RUST_TARGET_x86_64-linux-musl := x86_64-unknown-linux-musl
RUST_TARGET_aarch64-linux-musl := aarch64-unknown-linux-musl
RUST_TARGET_arm-linux-musleabihf := arm-unknown-linux-musleabihf
RUST_TARGET_riscv64-linux-musl := riscv64gc-unknown-linux-musl
RUST_TARGET := $(RUST_TARGET_$(ARCH))
RUST_DIST := rustc-$(RUST_VERSION)-$(RUST_HOST) cargo-$(RUST_VERSION)-$(RUST_HOST) \
	$(sort rust-std-$(RUST_VERSION)-$(RUST_HOST) rust-std-$(RUST_VERSION)-$(RUST_TARGET))
RUST_DIR := $(B)/rust
RUST_STAMP := $(RUST_DIR)/.installed
RUST_TARGET_ENV := $(subst -,_,$(RUST_TARGET))
RUST_CARGO_ENV := $(shell printf '%s' '$(RUST_TARGET_ENV)' | tr '[:lower:]' '[:upper:]')
RSVG_PATCHES := $(sort $(wildcard patches/$(RSVG)/*.patch))
MEDIA_INPUTS := $(sort $(wildcard execinfo/*))
LIBRARY_PATCHES += $(RSVG_PATCHES)

MEDIA_PACKAGES := $(PIXMAN) $(LIBPNG) $(LIBXML2) $(FONTCONFIG) $(FRIBIDI) $(CAIRO) $(PANGO) $(RSVG) $(ALSA)
MEDIA_ARCHIVES := $(addsuffix .tar.xz,$(filter-out $(LIBPNG) $(ALSA),$(MEDIA_PACKAGES)) $(RUST_DIST)) \
	$(LIBPNG).tar.gz $(ALSA).tar.bz2 $(CARGO_C).tar.gz
PACKAGES += $(MEDIA_PACKAGES)
ARCHIVES += $(MEDIA_ARCHIVES)

EXECINFO_OUTPUTS := $(T)/lib/libexecinfo.a $(T)/include/execinfo.h $(T)/lib/pkgconfig/execinfo.pc
PIXMAN_OUTPUTS := $(T)/lib/libpixman-1.a $(T)/include/pixman-1/pixman.h $(T)/lib/pkgconfig/pixman-1.pc
LIBPNG_OUTPUTS := $(T)/lib/libpng16.a $(T)/include/png.h $(T)/lib/pkgconfig/libpng.pc
LIBXML2_OUTPUTS := $(T)/lib/libxml2.a $(T)/include/libxml2/libxml/parser.h $(T)/lib/pkgconfig/libxml-2.0.pc
FONTCONFIG_OUTPUTS := $(T)/lib/libfontconfig.a $(T)/include/fontconfig/fontconfig.h \
	$(T)/lib/pkgconfig/fontconfig.pc $(T)/etc/fonts/fonts.conf
FRIBIDI_OUTPUTS := $(T)/lib/libfribidi.a $(T)/include/fribidi/fribidi.h $(T)/lib/pkgconfig/fribidi.pc
CAIRO_OUTPUTS := $(addprefix $(T)/lib/lib,$(addsuffix .a,cairo cairo-gobject)) \
	$(addprefix $(T)/include/cairo/,cairo.h cairo-gobject.h) \
	$(addprefix $(T)/lib/pkgconfig/,$(addsuffix .pc,cairo cairo-gobject cairo-png))
PANGO_OUTPUTS := $(addprefix $(T)/lib/lib,$(addsuffix -1.0.a,pango pangocairo pangoft2)) \
	$(addprefix $(T)/include/pango-1.0/pango/,pango.h pangocairo.h pangoft2.h) \
	$(addprefix $(T)/lib/pkgconfig/,$(addsuffix .pc,pango pangocairo pangoft2))
RSVG_OUTPUTS := $(T)/lib/librsvg-2.a $(T)/include/librsvg-2.0/librsvg/rsvg.h \
	$(T)/include/librsvg-2.0/librsvg/rsvg-cairo.h $(T)/lib/pkgconfig/librsvg-2.0.pc
ALSA_OUTPUTS := $(T)/lib/libasound.a $(T)/include/alsa/asoundlib.h \
	$(T)/lib/pkgconfig/alsa.pc $(T)/share/alsa/alsa.conf
MEDIA_OUTPUTS := $(EXECINFO_OUTPUTS) $(PIXMAN_OUTPUTS) $(LIBPNG_OUTPUTS) $(LIBXML2_OUTPUTS) \
	$(FONTCONFIG_OUTPUTS) $(FRIBIDI_OUTPUTS) $(CAIRO_OUTPUTS) $(PANGO_OUTPUTS) $(RSVG_OUTPUTS) \
	$(ALSA_OUTPUTS) $(T)/lib/libunwind.a
OUTPUTS += $(MEDIA_OUTPUTS)

MEDIA_CROSS := $(B)/media-cross.ini

$(MEDIA_CROSS): $(B)/config
	{ printf '%s\n' '[binaries]' \
		"c = [$(MESON_LAUNCHER)'$(TOOLCHAIN)/bin/$(ARCH)-gcc']" \
		"cpp = [$(MESON_LAUNCHER)'$(TOOLCHAIN)/bin/$(ARCH)-g++']" \
		"ar = '$(AR)'" "strip = '$(TOOLCHAIN)/bin/$(ARCH)-strip'" "pkg-config = 'pkg-config'"; \
	  printf '%s\n' '[host_machine]' "system = 'linux'" "endian = 'little'" \
		"cpu_family = '$(TARGET_CPU)'" "cpu = '$(TARGET_CPU)'"; \
	  printf '%s\n' '[properties]' 'needs_exe_wrapper = true' "pkg_config_libdir = '$(PKG_CONFIG_LIBDIR)'"; \
	} > "$@"

MEDIA_ENV = $(CACHE_ENV) env CFLAGS="$(CFLAGS)" CXXFLAGS="$(CXXFLAGS)" LDFLAGS="$(LDFLAGS) -L$(T)/lib"
# The unprepared compiler sysroot still contains shared libraries alongside archives.
media-setup = meson setup "$(B)/$(1)/build" "$(B)/$(1)" --cross-file "$(MEDIA_CROSS)" \
	--prefix "$(T)" --libdir lib --buildtype release --default-library static --wrap-mode nodownload \
	-Dprefer_static=true -Db_staticpic=true -Dpkgconfig.relocatable=true

define media-install
$(CACHE_ENV) meson compile -C "$(B)/$(1)/build" -j $(JOBS)
$(CACHE_ENV) meson install -C "$(B)/$(1)/build" --no-rebuild
endef

$(EXECINFO_OUTPUTS) &: $(B)/config $(MEDIA_INPUTS)
	mkdir -p "$(B)/execinfo" "$(T)/lib"
	$(AUTOCONF_ENV) $(CC) $(CFLAGS) -fPIC -funwind-tables -c execinfo/execinfo.c -o "$(B)/execinfo/execinfo.o"
	$(AR) rcs "$(T)/lib/libexecinfo.a" "$(B)/execinfo/execinfo.o"
	install -Dm644 execinfo/execinfo.h "$(T)/include/execinfo.h"
	install -Dm644 execinfo/execinfo.pc "$(T)/lib/pkgconfig/execinfo.pc"

$(PIXMAN_OUTPUTS) &: $(B)/$(PIXMAN)/.extracted $(MEDIA_CROSS)
	$(MEDIA_ENV) $(call media-setup,$(PIXMAN)) -Dtests=disabled -Ddemos=disabled -Dgtk=disabled -Dlibpng=disabled
	$(call media-install,$(PIXMAN))
	install -Dm644 "$(B)/$(PIXMAN)/COPYING" "$(T)/share/licenses/pixman/COPYING"

$(LIBPNG_OUTPUTS) &: $(B)/$(LIBPNG)/.extracted $(T)/lib/libz.a
	$(CACHE_ENV) cmake -S "$(B)/$(LIBPNG)" -B "$(B)/$(LIBPNG)/build" $(CMAKE_FLAGS) \
		-DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DZLIB_ROOT="$(T)" \
		-DPNG_SHARED=OFF -DPNG_STATIC=ON -DPNG_TESTS=OFF -DPNG_TOOLS=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(LIBPNG)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(LIBPNG)/build"
	install -Dm644 "$(B)/$(LIBPNG)/LICENSE" "$(T)/share/licenses/libpng/LICENSE"

$(LIBXML2_OUTPUTS) &: $(B)/$(LIBXML2)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(LIBXML2)" -B "$(B)/$(LIBXML2)/build" $(CMAKE_FLAGS) \
		-DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_SHARED_LIBS=OFF \
		-DLIBXML2_WITH_PROGRAMS=OFF -DLIBXML2_WITH_TESTS=OFF -DLIBXML2_WITH_MODULES=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(LIBXML2)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(LIBXML2)/build"
	install -Dm644 "$(B)/$(LIBXML2)/Copyright" "$(T)/share/licenses/libxml2/Copyright"

$(FONTCONFIG_OUTPUTS) &: $(B)/$(FONTCONFIG)/.extracted $(MEDIA_CROSS) $(FREETYPE_OUTPUTS) $(LIBXML2_OUTPUTS)
	$(MEDIA_ENV) $(call media-setup,$(FONTCONFIG)) \
		-Dxml-backend=libxml2 -Dcache-build=disabled -Ddoc=disabled -Dnls=disabled -Dtests=disabled -Dtools=disabled \
		-Dbaseconfig-dir=/etc/fonts -Dtemplate-dir=/etc/fonts/conf.avail -Dcache-dir=/var/cache/fontconfig
	$(CACHE_ENV) meson compile -C "$(B)/$(FONTCONFIG)/build" -j $(JOBS)
	$(CACHE_ENV) meson install -C "$(B)/$(FONTCONFIG)/build" --no-rebuild --destdir "$(B)/$(FONTCONFIG)/stage"
	mkdir -p "$(T)/etc"
	cp -a "$(B)/$(FONTCONFIG)/stage$(T)/." "$(T)/"
	cp -a "$(B)/$(FONTCONFIG)/stage/etc/fonts" "$(T)/etc/"
	install -Dm644 "$(B)/$(FONTCONFIG)/COPYING" "$(T)/share/licenses/fontconfig/COPYING"

$(FRIBIDI_OUTPUTS) &: $(B)/$(FRIBIDI)/.extracted $(MEDIA_CROSS)
	$(MEDIA_ENV) $(call media-setup,$(FRIBIDI)) -Dbin=false -Ddocs=false -Dtests=false
	$(call media-install,$(FRIBIDI))
	install -Dm644 "$(B)/$(FRIBIDI)/COPYING" "$(T)/share/licenses/fribidi/COPYING"

$(CAIRO_OUTPUTS) &: $(B)/$(CAIRO)/.extracted $(MEDIA_CROSS) $(PIXMAN_OUTPUTS) $(LIBPNG_OUTPUTS) \
	$(FONTCONFIG_OUTPUTS) $(FREETYPE_OUTPUTS) $(GLIB_OUTPUTS) $(T)/lib/libz.a
	$(MEDIA_ENV) $(call media-setup,$(CAIRO)) \
		-Dpng=enabled -Dglib=enabled -Dfontconfig=enabled -Dfreetype=enabled -Dzlib=enabled \
		-Dxlib=disabled -Dxcb=disabled -Dxlib-xcb=disabled -Dgtk2-utils=disabled \
		-Dlzo=disabled -Dspectre=disabled -Dtests=disabled
	$(call media-install,$(CAIRO))
	install -dm755 "$(T)/share/licenses/cairo"
	install -m644 "$(B)/$(CAIRO)"/COPYING* "$(T)/share/licenses/cairo/"

$(PANGO_OUTPUTS) &: $(B)/$(PANGO)/.extracted $(MEDIA_CROSS) $(CAIRO_OUTPUTS) $(FONTCONFIG_OUTPUTS) \
	$(FREETYPE_OUTPUTS) $(FRIBIDI_OUTPUTS) $(HARFBUZZ_OUTPUTS) $(GLIB_OUTPUTS)
	$(MEDIA_ENV) $(call media-setup,$(PANGO)) \
		-Dcairo=enabled -Dfontconfig=enabled -Dfreetype=enabled -Dlibthai=disabled -Dxft=disabled \
		-Dintrospection=disabled -Dbuild-testsuite=false -Dbuild-examples=false
	$(call media-install,$(PANGO))
	install -Dm644 "$(B)/$(PANGO)/COPYING" "$(T)/share/licenses/pango/COPYING"

$(RUST_STAMP): $(addsuffix /.extracted,$(addprefix $(B)/,$(RUST_DIST))) $(SOURCE_CACHE)/$(CARGO_C).tar.gz
	rm -rf "$(RUST_DIR)"
	mkdir -p "$(RUST_DIR)/bin"
	set -e; for dist in $(RUST_DIST); do \
		"$(B)/$$dist/install.sh" --prefix="$(RUST_DIR)" --disable-ldconfig; \
	done
	tar -xf "$(SOURCE_CACHE)/$(CARGO_C).tar.gz" -C "$(RUST_DIR)/bin" cargo-cbuild
	touch "$@"

$(T)/lib/libunwind.a: $(RUST_STAMP)
	install -Dm644 "$(RUST_DIR)/lib/rustlib/$(RUST_TARGET)/lib/self-contained/libunwind.a" "$@"
	install -dm755 "$(T)/share/licenses/rust-std"
	install -m644 "$(B)/rust-std-$(RUST_VERSION)-$(RUST_TARGET)"/COPYRIGHT \
		"$(B)/rust-std-$(RUST_VERSION)-$(RUST_TARGET)"/LICENSE-* "$(T)/share/licenses/rust-std/"

$(B)/$(RSVG)/.patched: $(B)/$(RSVG)/.extracted $(RSVG_PATCHES)
	@set -e; for source_patch in $(RSVG_PATCHES); do \
		patch --fuzz=0 -d "$(B)/$(RSVG)" -p1 < "$$source_patch"; \
	done
	touch "$@"

RSVG_ENV = env PATH="$(RUST_DIR)/bin:$$PATH" CARGO_HOME="$(CARGO_HOME)" CARGO_BUILD_JOBS="$(JOBS)" \
	RUSTFLAGS="-C target-feature=+crt-static -C link-self-contained=no -C relocation-model=pic" \
	CARGO_TARGET_$(RUST_CARGO_ENV)_LINKER="$(TOOLCHAIN)/bin/$(ARCH)-gcc" \
	CC_$(RUST_TARGET_ENV)="$(TOOLCHAIN)/bin/$(ARCH)-gcc" AR_$(RUST_TARGET_ENV)="$(AR)"

$(RSVG_OUTPUTS) &: $(B)/$(RSVG)/.patched $(MEDIA_CROSS) $(PANGO_OUTPUTS) $(LIBXML2_OUTPUTS) $(T)/lib/libunwind.a
	$(RSVG_ENV) cargo fetch --locked --manifest-path "$(B)/$(RSVG)/Cargo.toml" --target "$(RUST_TARGET)"
	$(MEDIA_ENV) $(RSVG_ENV) CARGO_NET_OFFLINE=true $(call media-setup,$(RSVG)) \
		-Dtriplet="$(RUST_TARGET)" -Davif=disabled -Dpixbuf=disabled -Dpixbuf-loader=disabled \
		-Dintrospection=disabled -Ddocs=disabled -Dvala=disabled -Drsvg-convert=disabled -Dtests=false
	$(CACHE_ENV) $(RSVG_ENV) CARGO_NET_OFFLINE=true meson compile -C "$(B)/$(RSVG)/build" -j $(JOBS)
	$(CACHE_ENV) $(RSVG_ENV) CARGO_NET_OFFLINE=true meson install -C "$(B)/$(RSVG)/build" --no-rebuild
	install -dm755 "$(T)/share/licenses/librsvg"
	install -m644 "$(B)/$(RSVG)"/COPYING.LIB "$(B)/$(RSVG)"/Cargo.lock "$(T)/share/licenses/librsvg/"

$(ALSA_OUTPUTS) &: $(B)/$(ALSA)/.extracted
	cd "$(B)/$(ALSA)" && $(AUTOCONF_ENV) CFLAGS="$(CFLAGS) -fPIC" \
		./configure --prefix="$(T)" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --enable-static --without-versioned --without-libdl \
		--disable-python --disable-aload --with-configdir=/usr/share/alsa
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(ALSA)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(ALSA)" install DESTDIR="$(B)/$(ALSA)/stage"
	cp -a "$(B)/$(ALSA)/stage$(T)/." "$(T)/"
	mkdir -p "$(T)/share"
	cp -a "$(B)/$(ALSA)/stage/usr/share/alsa" "$(T)/share/"
	sed -i 's|^prefix=.*|prefix=$${pcfiledir}/../..|' "$(T)/lib/pkgconfig/alsa.pc"
	install -Dm644 "$(B)/$(ALSA)/COPYING" "$(T)/share/licenses/alsa-lib/COPYING"
