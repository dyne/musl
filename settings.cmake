### CMake settings for the dyne/musl toolchain

# Configurable settings
set(ARCH "x86_64-linux-musl" CACHE STRING "Target architecture to (cross)compile")
set(CMAKE_CXX_FLAGS "-static -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow" CACHE STRING "C++ Compilation flags, default set for small and secure binaries")
set(CMAKE_C_FLAGS "-static -g0 -Os -fstack-protector-all -D_FORTIFY_SOURCE=2 -fno-strict-overflow" CACHE STRING "C Compilation flags, default set for small and secure binaries")
option(CCACHE "Use ccache to speed up compilation" 1)
option(FOR_MUSL_DYNE "Install target will copy everything inside /opt/musl-dyne" 0)
option(FORCE_STATIC "Force linker flags to build static executables (may fix or break some cases)" 0)

# No need to change anything below here
set(PREFIX "/opt/musl-dyne")
set(CMAKE_C_COMPILER "${PREFIX}/bin/${ARCH}-gcc")
set(CMAKE_CXX_COMPILER "${PREFIX}/bin/${ARCH}-g++")
set(CMAKE_ASM_COMPILER "${PREFIX}/bin/${ARCH}-as")

set(CMAKE_SYSROOT "${PREFIX}/${ARCH}")
set(CMAKE_PREFIX_PATH "${PREFIX};${PREFIX}/${ARCH}")
include_directories(SYSTEM "${PREFIX}/${ARCH}/include")

# Remove flags added by build type
set(CMAKE_BUILD_TYPE "Release")
set(CMAKE_CXX_FLAGS_RELEASE "")

function(echo msg)
    if(NOT DEFINED PRINT_ONCE_${msg})
        message(STATUS "${msg}")
        set(PRINT_ONCE_${msg} TRUE CACHE INTERNAL "Flag for first pass message printed")
    endif()
endfunction()
# Define escape sequence
string(ASCII 27 Esc)
set(Red     "${Esc}[31m")
set(Green   "${Esc}[32m")
set(Yellow  "${Esc}[33m")
set(Reset   "${Esc}[0m")



echo("💪 ${Green}Dyne / Musl toolchain configured${Reset}")
echo("💪 Build target architecture: ${ARCH}")

if(CCACHE)
  set(CMAKE_C_COMPILER_LAUNCHER "ccache")
  set(CMAKE_CXX_COMPILER_LAUNCHER "ccache")
  echo("💪 Using CCACHE to speed up build")
endif()

if(FOR_MUSL_DYNE)
  set(CMAKE_INSTALL_PREFIX "${PREFIX}/${ARCH}" CACHE PATH "Install path")
  echo("💪 Building to install inside /opt/musl-dyne")
endif()

if(FORCE_STATIC)
  set(CMAKE_EXE_LINKER_FLAGS "-static -static-libgcc -static-libstdc++")
  echo("💪 Forcing static compiler flags")
endif()
