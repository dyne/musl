cmake_minimum_required(VERSION 3.22)
project(DyneGioConsumer LANGUAGES C)

include("${CMAKE_CURRENT_LIST_DIR}/../cmake/RequireStaticPIE.cmake")
dyne_require_static_pie()
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(PkgConfig REQUIRED)
list(APPEND PKG_CONFIG_ARGN --static)
pkg_check_modules(GIO REQUIRED IMPORTED_TARGET gio-unix-2.0)
add_executable(glib-smoke main.c)
target_link_libraries(glib-smoke PRIVATE PkgConfig::GIO)
