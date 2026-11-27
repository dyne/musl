cmake_minimum_required(VERSION 3.22)
project(DyneMediaConsumers LANGUAGES C CXX)

include("${CMAKE_CURRENT_LIST_DIR}/../cmake/RequireStaticPIE.cmake")
dyne_require_static_pie()
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_FIND_LIBRARY_SUFFIXES .a)

find_package(PkgConfig REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
list(APPEND PKG_CONFIG_ARGN --dont-define-prefix --static)
pkg_check_modules(SVG REQUIRED IMPORTED_TARGET librsvg-2.0)
pkg_check_modules(EXECINFO REQUIRED IMPORTED_TARGET execinfo)
pkg_check_modules(ALSA REQUIRED IMPORTED_TARGET alsa)

add_executable(svg svg.c)
target_link_libraries(svg PRIVATE PkgConfig::SVG)
set(font "${CMAKE_CURRENT_BINARY_DIR}/smoke.ttf")
add_custom_command(OUTPUT "${font}"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../sdl/make-font.py" "${font}"
  DEPENDS ../sdl/make-font.py VERBATIM)
add_custom_target(svg-font DEPENDS "${font}")
add_dependencies(svg svg-font)

add_executable(execinfo execinfo.cpp)
target_compile_options(execinfo PRIVATE -funwind-tables -fno-optimize-sibling-calls)
target_link_libraries(execinfo PRIVATE PkgConfig::EXECINFO PkgConfig::SVG)

add_executable(alsa alsa.c)
target_link_libraries(alsa PRIVATE PkgConfig::ALSA)

enable_testing()
add_test(NAME svg COMMAND svg "${font}")
add_test(NAME execinfo COMMAND execinfo)
add_test(NAME alsa COMMAND alsa)
