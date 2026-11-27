FFMPEG ?= ffmpeg-9.1
DAV1D ?= dav1d-1.5.5
VPX ?= libvpx-1.17.0
JXL ?= libjxl-0.13.0
HWY ?= highway-1.4.0
BROTLI ?= brotli-1.2.1
LCMS2 ?= lcms2-2.20
ASS ?= libass-0.17.5
ZIMG ?= zimg-3.0.6
BZIP2 ?= bzip2-1.0.8
XZ ?= xz-5.8.4

FFMPEG_PACKAGES := $(FFMPEG) $(DAV1D) $(VPX) $(JXL) $(HWY) $(BROTLI) $(LCMS2) $(ASS) $(ZIMG) $(BZIP2) $(XZ)
FFMPEG_ARCHIVES := $(addsuffix .tar.xz,$(FFMPEG) $(DAV1D) $(ASS) $(XZ)) \
	$(addsuffix .tar.gz,$(VPX) $(JXL) $(HWY) $(BROTLI) $(LCMS2) $(ZIMG) $(BZIP2))
PACKAGES += $(FFMPEG_PACKAGES)
ARCHIVES += $(FFMPEG_ARCHIVES)

DAV1D_OUTPUTS := $(T)/lib/libdav1d.a $(T)/include/dav1d/dav1d.h $(T)/lib/pkgconfig/dav1d.pc
VPX_OUTPUTS := $(T)/lib/libvpx.a $(T)/include/vpx/vpx_decoder.h $(T)/lib/pkgconfig/vpx.pc
HWY_OUTPUTS := $(T)/lib/libhwy.a $(T)/include/hwy/highway.h $(T)/lib/pkgconfig/libhwy.pc \
	$(T)/lib/cmake/hwy/hwy-config.cmake
BROTLI_OUTPUTS := $(addprefix $(T)/lib/libbrotli,$(addsuffix .a,common dec enc)) \
	$(addprefix $(T)/lib/pkgconfig/libbrotli,$(addsuffix .pc,common dec enc)) $(T)/include/brotli/decode.h
LCMS2_OUTPUTS := $(T)/lib/liblcms2.a $(T)/include/lcms2.h $(T)/lib/pkgconfig/lcms2.pc
JXL_OUTPUTS := $(addprefix $(T)/lib/lib,$(addsuffix .a,jxl jxl_threads jxl_cms)) \
	$(addprefix $(T)/lib/pkgconfig/lib,$(addsuffix .pc,jxl jxl_threads jxl_cms)) $(T)/include/jxl/decode.h
ASS_OUTPUTS := $(T)/lib/libass.a $(T)/include/ass/ass.h $(T)/lib/pkgconfig/libass.pc
ZIMG_OUTPUTS := $(T)/lib/libzimg.a $(T)/include/zimg.h $(T)/lib/pkgconfig/zimg.pc
BZIP2_OUTPUTS := $(T)/lib/libbz2.a $(T)/include/bzlib.h
XZ_OUTPUTS := $(T)/lib/liblzma.a $(T)/include/lzma.h $(T)/lib/pkgconfig/liblzma.pc
FFMPEG_LIBS := avcodec avdevice avfilter avformat avutil swresample swscale
FFMPEG_OUTPUTS := $(T)/bin/ffmpeg $(T)/bin/ffprobe \
	$(addprefix $(T)/lib/lib,$(addsuffix .a,$(FFMPEG_LIBS))) \
	$(addprefix $(T)/lib/pkgconfig/lib,$(addsuffix .pc,$(FFMPEG_LIBS))) \
	$(foreach lib,$(FFMPEG_LIBS),$(T)/include/lib$(lib)/$(lib).h) \
	$(T)/share/licenses/ffmpeg/COPYING.LGPLv2.1
OUTPUTS += $(DAV1D_OUTPUTS) $(VPX_OUTPUTS) $(HWY_OUTPUTS) $(BROTLI_OUTPUTS) $(LCMS2_OUTPUTS) \
	$(JXL_OUTPUTS) $(ASS_OUTPUTS) $(ZIMG_OUTPUTS) $(BZIP2_OUTPUTS) $(XZ_OUTPUTS) $(FFMPEG_OUTPUTS)

FFMPEG_CMAKE_FLAGS = $(CMAKE_FLAGS) -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_SHARED_LIBS=OFF \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON -DBUILD_TESTING=OFF
FFMPEG_CROSS := $(TOOLCHAIN)/bin/$(ARCH)-
# Keep the SDK's ARM hard-float CPU baseline while using assembly where supported.
VPX_TARGET_x86_64-linux-musl := x86_64-linux-gcc
VPX_TARGET_aarch64-linux-musl := arm64-linux-gcc
VPX_TARGET = $(or $(VPX_TARGET_$(ARCH)),generic-gnu)

$(DAV1D_OUTPUTS) &: $(B)/$(DAV1D)/.extracted $(MEDIA_CROSS)
	$(MEDIA_ENV) $(call media-setup,$(DAV1D)) -Denable_tools=false -Denable_tests=false \
		-Denable_asm=$(if $(filter arm,$(TARGET_CPU)),false,true)
	$(call media-install,$(DAV1D))
	install -Dm644 "$(B)/$(DAV1D)/COPYING" "$(T)/share/licenses/dav1d/COPYING"

# libvpx uses TOOLCHAIN for its target name. Keep the SDK prefix out of its Makefiles.
$(VPX_OUTPUTS) &: $(B)/$(VPX)/.extracted
	cd "$(B)/$(VPX)" && $(AUTOCONF_ENV) CROSS="$(FFMPEG_CROSS)" \
		./configure --prefix="$(T)" --libdir="$(T)/lib" --target=$(VPX_TARGET) \
		--enable-static --disable-shared --enable-pic --extra-cflags="$(CFLAGS)" \
		--disable-examples --disable-tools --disable-docs --disable-unit-tests \
		--disable-vp8-encoder --disable-vp9-encoder
	$(CACHE_ENV) env -u MAKEFLAGS -u TOOLCHAIN $(MAKE) -C "$(B)/$(VPX)" -j$(JOBS)
	$(CACHE_ENV) env -u MAKEFLAGS -u TOOLCHAIN $(MAKE) -C "$(B)/$(VPX)" install
	install -dm755 "$(T)/share/licenses/libvpx"
	install -m644 "$(B)/$(VPX)"/LICENSE "$(B)/$(VPX)"/PATENTS "$(T)/share/licenses/libvpx/"

$(HWY_OUTPUTS) &: $(B)/$(HWY)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(HWY)" -B "$(B)/$(HWY)/build" $(FFMPEG_CMAKE_FLAGS) \
		-DHWY_ENABLE_CONTRIB=OFF -DHWY_ENABLE_TESTS=OFF -DHWY_ENABLE_EXAMPLES=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(HWY)/build" --target hwy --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(HWY)/build"
	install -Dm644 "$(B)/$(HWY)/LICENSE" "$(T)/share/licenses/highway/LICENSE"

$(BROTLI_OUTPUTS) &: $(B)/$(BROTLI)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(BROTLI)" -B "$(B)/$(BROTLI)/build" $(FFMPEG_CMAKE_FLAGS) \
		-DBROTLI_DISABLE_TESTS=ON -DBROTLI_BUILD_TOOLS=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(BROTLI)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(BROTLI)/build"
	install -Dm644 "$(B)/$(BROTLI)/LICENSE" "$(T)/share/licenses/brotli/LICENSE"

$(LCMS2_OUTPUTS) &: $(B)/$(LCMS2)/.extracted
	cd "$(B)/$(LCMS2)" && $(AUTOCONF_ENV) CFLAGS="$(CFLAGS) -fPIC" \
		./configure --prefix="$(T)" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --enable-static --with-pic --without-jpeg --without-tiff
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(LCMS2)/src" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(LCMS2)/src" install
	$(MAKE) -C "$(B)/$(LCMS2)/include" install
	$(MAKE) -C "$(B)/$(LCMS2)" install-pkgconfigDATA
	install -Dm644 "$(B)/$(LCMS2)/LICENSE" "$(T)/share/licenses/lcms2/LICENSE"

$(JXL_OUTPUTS) &: $(B)/$(JXL)/.extracted $(HWY_OUTPUTS) $(BROTLI_OUTPUTS) $(LCMS2_OUTPUTS)
	$(CACHE_ENV) cmake -S "$(B)/$(JXL)" -B "$(B)/$(JXL)/build" $(FFMPEG_CMAKE_FLAGS) \
		-DJPEGXL_FORCE_SYSTEM_HWY=ON -DJPEGXL_FORCE_SYSTEM_BROTLI=ON -DJPEGXL_FORCE_SYSTEM_LCMS2=ON \
		-DJPEGXL_ENABLE_SKCMS=OFF -DJPEGXL_ENABLE_TOOLS=OFF -DJPEGXL_ENABLE_EXAMPLES=OFF \
		-DJPEGXL_ENABLE_BENCHMARK=OFF -DJPEGXL_ENABLE_MANPAGES=OFF -DJPEGXL_ENABLE_DOXYGEN=OFF \
		-DJPEGXL_ENABLE_OPENEXR=OFF -DJPEGXL_ENABLE_TCMALLOC=OFF -DJPEGXL_ENABLE_SJPEG=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(JXL)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(JXL)/build"
	install -dm755 "$(T)/share/licenses/libjxl"
	install -m644 "$(B)/$(JXL)"/LICENSE "$(B)/$(JXL)"/PATENTS "$(T)/share/licenses/libjxl/"

$(ASS_OUTPUTS) &: $(B)/$(ASS)/.extracted $(FONTCONFIG_OUTPUTS) $(FRIBIDI_OUTPUTS) $(HARFBUZZ_OUTPUTS) $(FREETYPE_OUTPUTS)
	cd "$(B)/$(ASS)" && $(AUTOCONF_ENV) CFLAGS="$(CFLAGS) -fPIC" PKG_CONFIG="pkg-config --static" \
		./configure --prefix="$(T)" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --enable-static --with-pic --enable-fontconfig --disable-libunibreak
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(ASS)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(ASS)" install
	install -Dm644 "$(B)/$(ASS)/COPYING" "$(T)/share/licenses/libass/COPYING"

$(ZIMG_OUTPUTS) &: $(B)/$(ZIMG)/.extracted
	cd "$(B)/$(ZIMG)" && ./autogen.sh && $(AUTOCONF_ENV) CXXFLAGS="$(CXXFLAGS) -fPIC" \
		./configure --prefix="$(T)" --build=x86_64-linux-musl --host=$(ARCH) \
		--disable-shared --enable-static --with-pic
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(ZIMG)" -j$(JOBS)
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(ZIMG)" install
	install -Dm644 "$(B)/$(ZIMG)/COPYING" "$(T)/share/licenses/zimg/COPYING"

$(BZIP2_OUTPUTS) &: $(B)/$(BZIP2)/.extracted
	$(CACHE_ENV) $(MAKE) -C "$(B)/$(BZIP2)" -j$(JOBS) libbz2.a \
		CC="$(CC)" AR="$(AR)" RANLIB="$(RANLIB)" CFLAGS="$(CFLAGS) -fPIC -D_FILE_OFFSET_BITS=64"
	install -Dm644 "$(B)/$(BZIP2)/libbz2.a" "$(T)/lib/libbz2.a"
	install -Dm644 "$(B)/$(BZIP2)/bzlib.h" "$(T)/include/bzlib.h"
	install -Dm644 "$(B)/$(BZIP2)/LICENSE" "$(T)/share/licenses/bzip2/LICENSE"

$(XZ_OUTPUTS) &: $(B)/$(XZ)/.extracted
	$(CACHE_ENV) cmake -S "$(B)/$(XZ)" -B "$(B)/$(XZ)/build" $(FFMPEG_CMAKE_FLAGS) \
		-DXZ_TOOL_XZ=OFF -DXZ_TOOL_XZDEC=OFF -DXZ_TOOL_LZMADEC=OFF -DXZ_TOOL_LZMAINFO=OFF \
		-DXZ_DOC=OFF -DXZ_NLS=OFF
	$(CACHE_ENV) cmake --build "$(B)/$(XZ)/build" --parallel $(JOBS)
	$(CACHE_ENV) cmake --install "$(B)/$(XZ)/build"
	install -dm755 "$(T)/share/licenses/xz"
	install -m644 "$(B)/$(XZ)"/COPYING* "$(T)/share/licenses/xz/"

# FFmpeg selects architecture-specific objects using its configured ARCH.
$(FFMPEG_OUTPUTS) &: $(B)/$(FFMPEG)/.extracted $(DAV1D_OUTPUTS) $(VPX_OUTPUTS) $(JXL_OUTPUTS) \
	$(ASS_OUTPUTS) $(ZIMG_OUTPUTS) $(BZIP2_OUTPUTS) $(XZ_OUTPUTS) $(RSVG_OUTPUTS) $(GNUTLS_OUTPUTS) \
	$(FREETYPE_OUTPUTS) $(HARFBUZZ_OUTPUTS) $(FONTCONFIG_OUTPUTS) $(FRIBIDI_OUTPUTS) $(LIBXML2_OUTPUTS) $(T)/lib/libz.a
	cd "$(B)/$(FFMPEG)" && $(CACHE_ENV) ./configure --prefix="$(T)" --libdir="$(T)/lib" \
		--arch=$(TARGET_CPU) --target-os=linux --enable-cross-compile --cross-prefix="$(FFMPEG_CROSS)" \
		--cc="$(strip $(CCACHE_LAUNCHER) $(FFMPEG_CROSS)gcc)" \
		--cxx="$(strip $(CCACHE_LAUNCHER) $(FFMPEG_CROSS)g++)" \
		--pkg-config=pkg-config --pkg-config-flags=--static \
		--extra-cflags="$(CFLAGS) -I$(T)/include" --extra-cxxflags="$(CXXFLAGS) -I$(T)/include" \
		--extra-ldflags="$(LDFLAGS) -L$(T)/lib" --extra-libs="-lstdc++ -lm" \
		--enable-pic --enable-static --disable-shared --disable-autodetect --enable-pthreads \
		--disable-ffplay --disable-devices --disable-debug --disable-doc --disable-encoders \
		--enable-encoder=rawvideo,wrapped_avframe,pcm_s16le,pcm_f32le,png \
		--enable-libdav1d --enable-libvpx --enable-libjxl --enable-librsvg --enable-libass \
		--enable-libfreetype --enable-libharfbuzz --enable-libfontconfig --enable-libfribidi \
		--enable-libzimg --enable-gnutls --enable-libxml2 --enable-iconv --enable-zlib \
		--enable-bzlib --enable-lzma
	$(CACHE_ENV) env -u MAKEFLAGS -u ARCH $(MAKE) -C "$(B)/$(FFMPEG)" -j$(JOBS)
	$(CACHE_ENV) env -u MAKEFLAGS -u ARCH $(MAKE) -C "$(B)/$(FFMPEG)" install
	install -dm755 "$(T)/share/licenses/ffmpeg"
	install -m644 "$(B)/$(FFMPEG)"/LICENSE.md "$(B)/$(FFMPEG)"/COPYING.LGPLv2.1 "$(T)/share/licenses/ffmpeg/"
