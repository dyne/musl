cmake_minimum_required(VERSION 3.22)
project(DyneUuidConsumer LANGUAGES C)

include("${CMAKE_CURRENT_LIST_DIR}/../cmake/RequireStaticPIE.cmake")
dyne_require_static_pie()
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(PkgConfig REQUIRED)
list(APPEND PKG_CONFIG_ARGN --dont-define-prefix --static)
pkg_check_modules(UUID REQUIRED IMPORTED_TARGET uuid)
add_executable(uuid-smoke main.c)
target_link_libraries(uuid-smoke PRIVATE PkgConfig::UUID)
