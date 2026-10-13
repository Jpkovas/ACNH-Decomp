cmake_minimum_required(VERSION 3.25)
project(acnh_windows_translated_module LANGUAGES C CXX)
if(NOT WIN32 OR NOT CMAKE_C_COMPILER_ID STREQUAL "Clang")
  message(FATAL_ERROR "Use the pinned Windows llvm-mingw Clang toolchain")
endif()
set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT DEFINED GENERATED_DIR OR NOT DEFINED SCARLET_DIR OR NOT DEFINED GAME_OUTPUT)
  message(FATAL_ERROR "GENERATED_DIR, SCARLET_DIR and GAME_OUTPUT are required")
endif()
foreach(path GENERATED_DIR SCARLET_DIR GAME_OUTPUT)
  file(TO_CMAKE_PATH "${${path}}" ${path})
endforeach()
file(GLOB generated CONFIGURE_DEPENDS "${GENERATED_DIR}/*.c")
if(NOT generated)
  message(FATAL_ERROR "Generate the private ACNH C sources first")
endif()
add_library(acnh_code SHARED ${generated}
  ../reconstructed/src/identifier_hash.cpp ../reconstructed/src/constant_zero.cpp ../reconstructed/src/npad_full_key.cpp
  ../reconstructed/src/flag_int.cpp)
target_include_directories(acnh_code PRIVATE "${SCARLET_DIR}/runtime/abi" ../reconstructed/include)
# O0 produced an image over 2 GiB that Windows rejected with error 193.
# Keep object files in this incremental build so failed runs can resume.
target_compile_options(acnh_code PRIVATE -O1 -march=native -mtune=native
  -fno-strict-aliasing -fwrapv -mcx16 -foptimize-sibling-calls
  -fno-semantic-interposition -w)
target_link_options(acnh_code PRIVATE -static)
set_target_properties(acnh_code PROPERTIES PREFIX "" OUTPUT_NAME "ACNH_1_0_0_code"
  RUNTIME_OUTPUT_DIRECTORY "${GAME_OUTPUT}")
