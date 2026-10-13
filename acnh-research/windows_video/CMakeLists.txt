cmake_minimum_required(VERSION 3.25)
project(acnh_windows_video_fixture LANGUAGES C)
set(CMAKE_C_STANDARD 11)
set(SNX_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/ScarletNX")
set(FFMPEG_PREFIX "${CMAKE_CURRENT_SOURCE_DIR}/../build/windows-bridge/vulkan/ffmpeg" CACHE PATH "Built private FFmpeg libraries")
set(NVDEC_SOURCE "${SNX_ROOT}/runtime/video/nvdec.c" CACHE FILEPATH "NVDEC source under test")
# COFF resolves unrelated GPU-thread symbols before dead-code removal. Compile the
# unchanged swizzle function from the current runtime source in the fixture instead.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${SNX_ROOT}/runtime/gpu/gpu.c")
file(READ "${SNX_ROOT}/runtime/gpu/gpu.c" GPU_SOURCE)
string(REGEX MATCH "u64 bl_offset\\([^}]+\\}" BLOCK_LINEAR_FUNCTION "${GPU_SOURCE}")
if(NOT BLOCK_LINEAR_FUNCTION)
    message(FATAL_ERROR "Cannot locate runtime block-linear function for video fixture")
endif()
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/runtime_block_linear.c"
    "/* SwitchRecomp - Copyright 2026 MZ Labs. Apache-2.0, see vendor/ScarletNX/LICENSE.apache and NOTICE.\n"
    "   Fork changes GPL-3.0-or-later, see vendor/ScarletNX/LICENSE. Generated unchanged from runtime/gpu/gpu.c. */\n"
    "#include \"gpu/gpu.h\"\n${BLOCK_LINEAR_FUNCTION}\n")
add_executable(acnh-video-fixture nvdec_fixture.c
    "${NVDEC_SOURCE}"
    "${SNX_ROOT}/runtime/video/vic.c"
    "${CMAKE_CURRENT_BINARY_DIR}/runtime_block_linear.c")
# Fill the NVDEC packet allocation with a sentinel so required zero padding is observable.
set_source_files_properties("${NVDEC_SOURCE}" PROPERTIES COMPILE_DEFINITIONS realloc=fixture_realloc)
target_include_directories(acnh-video-fixture PRIVATE "${SNX_ROOT}/runtime" "${FFMPEG_PREFIX}/include")
target_compile_definitions(acnh-video-fixture PRIVATE _CRT_SECURE_NO_WARNINGS)
target_compile_options(acnh-video-fixture PRIVATE -Wall -Wextra -Werror -ffunction-sections -fdata-sections)
target_link_options(acnh-video-fixture PRIVATE -Wl,--gc-sections -Wl,--exclude-all-symbols)
target_link_libraries(acnh-video-fixture PRIVATE
    "${FFMPEG_PREFIX}/lib/libavcodec.a" "${FFMPEG_PREFIX}/lib/libswresample.a"
    "${FFMPEG_PREFIX}/lib/libavutil.a" bcrypt)
