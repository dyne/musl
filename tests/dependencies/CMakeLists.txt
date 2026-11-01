cmake_minimum_required(VERSION 3.22)
project(DyneDependencySmoke LANGUAGES C CXX)
include(CheckPIESupported)
check_pie_supported()
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Exercise the installed package metadata used by Bitcoin Core, rather than
# substituting include/library paths that could hide a broken SDK package.
find_package(Boost 1.74 CONFIG REQUIRED)
find_package(SQLite3 3.7.17 REQUIRED)
find_package(ZeroMQ 4.0 CONFIG REQUIRED)
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(SODIUM REQUIRED IMPORTED_TARGET libsodium)
if(TARGET SQLite3::SQLite3)
  set(sqlite_target SQLite3::SQLite3)
else()
  set(sqlite_target SQLite::SQLite3)
endif()
add_executable(dependencies main.cpp)
target_compile_features(dependencies PRIVATE cxx_std_20)
target_link_libraries(dependencies PRIVATE Boost::headers ${sqlite_target} libzmq-static PkgConfig::SODIUM Threads::Threads)

# Independently check the documented pkg-config --static interface from C,
# including libstdc++ and the crypto dependency closure.
list(APPEND PKG_CONFIG_ARGN --static)
pkg_check_modules(SDK_STATIC REQUIRED IMPORTED_TARGET libzmq sqlite3)
add_executable(pkgconfig pkgconfig.c)
target_link_libraries(pkgconfig PRIVATE PkgConfig::SDK_STATIC)

# avena's core/WebSocket modules have no external libraries. Its TLS module
# needs the OpenSSL-compatible static SSL/crypto interface supplied by LibreSSL.
set(OPENSSL_USE_STATIC_LIBS TRUE)
find_package(OpenSSL 1.1 REQUIRED)
add_executable(avena-dependencies avena.cpp)
# Match avena's static executable linkage; LibreSSL archives need not be PIC.
set_target_properties(avena-dependencies PROPERTIES POSITION_INDEPENDENT_CODE OFF)
target_compile_features(avena-dependencies PRIVATE cxx_std_17)
target_link_libraries(avena-dependencies PRIVATE OpenSSL::SSL OpenSSL::Crypto
  Threads::Threads ${CMAKE_DL_LIBS} atomic)
