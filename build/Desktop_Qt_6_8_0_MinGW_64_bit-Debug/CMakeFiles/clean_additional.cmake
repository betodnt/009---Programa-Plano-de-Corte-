# Additional clean files
cmake_minimum_required(VERSION 3.16)

if("${CONFIG}" STREQUAL "" OR "${CONFIG}" STREQUAL "Debug")
  file(REMOVE_RECURSE
  "CMakeFiles\\ControleCorteDobra_autogen.dir\\AutogenUsed.txt"
  "CMakeFiles\\ControleCorteDobra_autogen.dir\\ParseCache.txt"
  "ControleCorteDobra_autogen"
  )
endif()
