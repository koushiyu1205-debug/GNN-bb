cmake_minimum_required(VERSION 3.26)

project(lunar_spprc_native LANGUAGES CXX)

include(FetchContent)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(LUNAR_SPPRC_RCSPP_COMMIT
    "2f1d53ba6806844e30ce43ee9c41041a5a1b4e79"
    CACHE STRING "Pinned lab-core/rcspp commit")
set(LUNAR_SPPRC_PYTHON_INSTALL_DIR "" CACHE PATH "Python extension install directory")
option(
    LUNAR_SPPRC_ENABLE_NG_DSSR_V3
    "Compile the isolated ng-DSSR V3 development candidate"
    OFF
)
option(
    LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
    "Compile the isolated P0V4 bidirectional feasibility probe"
    OFF
)

set(SKBUILD ON CACHE BOOL "Disable upstream developer-only clang-tidy configuration" FORCE)
set(USE_TESTS OFF CACHE BOOL "Do not build upstream data-dependent tests" FORCE)
set(USE_PYTHON OFF CACHE BOOL "Use the project-local pybind layer" FORCE)
set(USE_VRP OFF CACHE BOOL "Do not build upstream examples" FORCE)

FetchContent_Declare(
    rcspp
    GIT_REPOSITORY https://github.com/lab-core/rcspp.git
    GIT_TAG ${LUNAR_SPPRC_RCSPP_COMMIT}
    GIT_SHALLOW FALSE
)
FetchContent_MakeAvailable(rcspp)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_VARIABLE LUNAR_SPPRC_PYBIND11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE LUNAR_SPPRC_PYBIND11_DISCOVERY_STATUS
)
if(LUNAR_SPPRC_PYBIND11_DISCOVERY_STATUS EQUAL 0 AND LUNAR_SPPRC_PYBIND11_CMAKE_DIR)
    list(APPEND CMAKE_PREFIX_PATH "${LUNAR_SPPRC_PYBIND11_CMAKE_DIR}")
endif()
find_package(pybind11 CONFIG REQUIRED)

add_library(lunar_spprc_core STATIC
    src/native_pricer.cpp
)
if(LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY)
    target_sources(
        lunar_spprc_core
        PRIVATE src/bidirectional_feasibility.cpp
    )
endif()
set_target_properties(lunar_spprc_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(lunar_spprc_core PUBLIC include)
target_include_directories(lunar_spprc_core SYSTEM PUBLIC "${rcspp_SOURCE_DIR}/cpp")
target_link_libraries(lunar_spprc_core PUBLIC rcspp rcspp_objects)
add_dependencies(lunar_spprc_core generate_umbrella_header)
target_compile_definitions(lunar_spprc_core PUBLIC
    LUNAR_SPPRC_RCSPP_COMMIT="${LUNAR_SPPRC_RCSPP_COMMIT}"
    LUNAR_SPPRC_BUILD_TYPE="${CMAKE_BUILD_TYPE}"
    LUNAR_SPPRC_ENABLE_NG_DSSR_V3=$<BOOL:${LUNAR_SPPRC_ENABLE_NG_DSSR_V3}>
    LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY=$<BOOL:${LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY}>
)

pybind11_add_module(lunar_spprc_native src/pybind_module.cpp)
target_link_libraries(lunar_spprc_native PRIVATE lunar_spprc_core)

enable_testing()
add_executable(lunar_spprc_native_tests tests/test_native_pricer.cpp)
target_link_libraries(lunar_spprc_native_tests PRIVATE lunar_spprc_core)
add_test(NAME lunar_spprc_native_tests COMMAND lunar_spprc_native_tests)
add_test(
    NAME lunar_spprc_patch_queue_check
    COMMAND "${Python_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/../../scripts/check_rcspp_patch_queue.py"
            --source "${rcspp_SOURCE_DIR}"
)

if(LUNAR_SPPRC_PYTHON_INSTALL_DIR)
    install(TARGETS lunar_spprc_native LIBRARY DESTINATION "${LUNAR_SPPRC_PYTHON_INSTALL_DIR}")
else()
    install(TARGETS lunar_spprc_native LIBRARY DESTINATION .)
endif()
