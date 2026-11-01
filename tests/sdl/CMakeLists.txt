cmake_minimum_required(VERSION 3.22)
project(DyneSDLConsumer LANGUAGES C CXX)
# Test static pkg-config exports even with an unprepared compiler sysroot that
# still contains libstdc++.so. Prepared release packages prune those DSOs.
set(CMAKE_FIND_LIBRARY_SUFFIXES .a)
include(CheckPIESupported)
check_pie_supported()
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
find_package(SDL3 3.4 CONFIG REQUIRED COMPONENTS SDL3-static)
find_package(SDL3_image 3.4 CONFIG REQUIRED COMPONENTS SDL3_image-static)
find_package(SDL3_ttf 3.2 CONFIG REQUIRED COMPONENTS SDL3_ttf-static)
find_package(harfbuzz CONFIG REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
add_custom_command(OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/smoke.ttf"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/make-font.py" "${CMAKE_CURRENT_BINARY_DIR}/smoke.ttf"
  DEPENDS make-font.py VERBATIM)
add_custom_target(sdl-font DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/smoke.ttf")
add_executable(sdl main.cpp)
target_compile_features(sdl PRIVATE cxx_std_17)
target_link_libraries(sdl PRIVATE SDL3_ttf::SDL3_ttf-static SDL3_image::SDL3_image-static
  SDL3::SDL3-static harfbuzz::harfbuzz)
add_dependencies(sdl sdl-font)
# Independently test pkg-config's complete static closure after relocation.
list(APPEND PKG_CONFIG_ARGN --static)
pkg_check_modules(SDL_STATIC REQUIRED IMPORTED_TARGET sdl3-image sdl3-ttf harfbuzz)
add_executable(sdl-pkgconfig pkgconfig.c)
target_link_libraries(sdl-pkgconfig PRIVATE PkgConfig::SDL_STATIC)
add_dependencies(sdl-pkgconfig sdl-font)
enable_testing()
foreach(consumer sdl sdl-pkgconfig)
  add_test(NAME ${consumer} COMMAND ${consumer} "${CMAKE_CURRENT_BINARY_DIR}/smoke.ttf")
  set_tests_properties(${consumer} PROPERTIES TIMEOUT 30 RUN_SERIAL TRUE)
endforeach()
