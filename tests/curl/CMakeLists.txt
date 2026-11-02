cmake_minimum_required(VERSION 3.22)
project(MuslActionSmoke LANGUAGES C CXX)
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
# Disable pkgconf's optional automatic prefix repair so broken archive metadata
# cannot be hidden by the host's particular pkg-config implementation.
list(APPEND PKG_CONFIG_ARGN --dont-define-prefix)
pkg_check_modules(CURL_PC REQUIRED libcurl)
add_executable(curl-pkgconfig main.cpp)
target_compile_features(curl-pkgconfig PRIVATE cxx_std_20)
target_include_directories(curl-pkgconfig PRIVATE ${CURL_PC_STATIC_INCLUDE_DIRS})
target_compile_options(curl-pkgconfig PRIVATE ${CURL_PC_STATIC_CFLAGS_OTHER})
target_link_libraries(curl-pkgconfig PRIVATE ${CURL_PC_STATIC_LDFLAGS} Threads::Threads)

set(OPENSSL_USE_STATIC_LIBS TRUE)
find_package(CURL CONFIG REQUIRED)
add_executable(curl-config main.cpp)
target_compile_features(curl-config PRIVATE cxx_std_20)
target_link_libraries(curl-config PRIVATE CURL::libcurl Threads::Threads)
