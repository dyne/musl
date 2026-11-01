cmake_minimum_required(VERSION 3.22)
project(DyneImGui VERSION ${IMGUI_VERSION} LANGUAGES CXX)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)
find_package(SDL3 3.4 CONFIG REQUIRED COMPONENTS SDL3-static)
if(NOT EXISTS "${IMGUI_SOURCE_DIR}/imgui.cpp")
  message(FATAL_ERROR "IMGUI_SOURCE_DIR must point to the verified upstream source")
endif()
add_library(imgui STATIC
  "${IMGUI_SOURCE_DIR}/imgui.cpp"
  "${IMGUI_SOURCE_DIR}/imgui_draw.cpp"
  "${IMGUI_SOURCE_DIR}/imgui_tables.cpp"
  "${IMGUI_SOURCE_DIR}/imgui_widgets.cpp"
  "${IMGUI_SOURCE_DIR}/imgui_demo.cpp"
  "${IMGUI_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp"
  "${IMGUI_SOURCE_DIR}/backends/imgui_impl_sdlrenderer3.cpp")
add_library(imgui::imgui ALIAS imgui)
target_compile_features(imgui PUBLIC cxx_std_11)
target_link_libraries(imgui PUBLIC SDL3::SDL3-static)
target_include_directories(imgui PUBLIC
  $<BUILD_INTERFACE:${IMGUI_SOURCE_DIR}>
  $<BUILD_INTERFACE:${IMGUI_SOURCE_DIR}/backends>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/imgui>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/imgui/backends>)
install(TARGETS imgui EXPORT imguiTargets ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES "${IMGUI_SOURCE_DIR}/imgui.h" "${IMGUI_SOURCE_DIR}/imconfig.h"
  "${IMGUI_SOURCE_DIR}/imgui_internal.h" "${IMGUI_SOURCE_DIR}/imstb_rectpack.h"
  "${IMGUI_SOURCE_DIR}/imstb_textedit.h" "${IMGUI_SOURCE_DIR}/imstb_truetype.h"
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/imgui)
install(FILES "${IMGUI_SOURCE_DIR}/backends/imgui_impl_sdl3.h"
  "${IMGUI_SOURCE_DIR}/backends/imgui_impl_sdlrenderer3.h"
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/imgui/backends)
install(EXPORT imguiTargets NAMESPACE imgui:: DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/imgui)
configure_package_config_file(imguiConfig.cmake.in "${CMAKE_CURRENT_BINARY_DIR}/imguiConfig.cmake"
  INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/imgui)
write_basic_package_version_file("${CMAKE_CURRENT_BINARY_DIR}/imguiConfigVersion.cmake"
  VERSION ${PROJECT_VERSION} COMPATIBILITY SameMajorVersion)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/imguiConfig.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/imguiConfigVersion.cmake" DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/imgui)
configure_file(imgui.pc.in "${CMAKE_CURRENT_BINARY_DIR}/imgui.pc" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/imgui.pc" DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig)
install(FILES "${IMGUI_SOURCE_DIR}/LICENSE.txt" DESTINATION ${CMAKE_INSTALL_DATADIR}/licenses/imgui)
# Preserve notices for the bundled font rasterizer and embedded default font.
install(FILES "${IMGUI_SOURCE_DIR}/imstb_truetype.h" "${IMGUI_SOURCE_DIR}/imgui_draw.cpp"
  DESTINATION ${CMAKE_INSTALL_DATADIR}/licenses/imgui)
