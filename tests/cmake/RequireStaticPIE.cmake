# CMake 3.x passes its PIE options only at link time when probing support.
# ARM/RISC-V objects using the stack protector must also be compiled with
# -fPIE; otherwise a valid static-PIE compiler is incorrectly rejected.
include(CheckPIESupported)

function(dyne_require_static_pie)
  # Function scope preserves the caller's feature-check flags afterward.
  string(APPEND CMAKE_REQUIRED_FLAGS " -fPIE")
  get_property(languages GLOBAL PROPERTY ENABLED_LANGUAGES)
  list(FILTER languages INCLUDE REGEX "^(C|CXX)$")
  check_pie_supported(OUTPUT_VARIABLE errors LANGUAGES ${languages})
  foreach(language IN LISTS languages)
    if(NOT CMAKE_${language}_LINK_PIE_SUPPORTED)
      message(FATAL_ERROR "Static PIE link support is required for ${language}:\n${errors}")
    endif()
  endforeach()
endfunction()
