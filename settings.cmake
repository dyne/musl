# CMake settings for the dyne/musl toolchain

set(ARCH "x86_64-linux-musl" CACHE STRING "Target architecture to (cross)compile")
set(PREFIX "/opt/musl-dyne")
set(CMAKE_CXX_FLAGS "-static -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow")
# -I ${PREFIX}/${ARCH}/include
include_directories(SYSTEM "${PREFIX}/${ARCH}/include")
# set(CMAKE_PREFIX_PATH "${PREFIX}/${ARCH}")
set(CMAKE_SYSROOT "${PREFIX}/${ARCH}")
set(CMAKE_PREFIX_PATH "${PREFIX};${PREFIX}/${ARCH}")

# Remove flags added by build type
set(CMAKE_BUILD_TYPE "Release")
set(CMAKE_CXX_FLAGS_RELEASE "")
set(CMAKE_C_COMPILER "${PREFIX}/bin/${ARCH}-gcc")
set(CMAKE_CXX_COMPILER "${PREFIX}/bin/${ARCH}-g++")

option(CCACHE "Use ccache to speed up compilation" ON)
if(CCACHE)
  set(CMAKE_CXX_COMPILER_LAUNCHER "ccache")
endif()
