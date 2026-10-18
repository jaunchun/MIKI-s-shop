cmake_minimum_required(VERSION 3.20)
project(MIKI_s_shop LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
set(PYBIND11_FINDPYTHON ON)

include(FetchContent)
set(FETCHCONTENT_UPDATES_DISCONNECTED ON)

set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(glew-cmake_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(glew-cmake_BUILD_STATIC ON  CACHE BOOL "" FORCE)
set(ONLY_LIBS ON CACHE BOOL "" FORCE)

FetchContent_Declare(glfw     GIT_REPOSITORY https://github.com/glfw/glfw.git           GIT_TAG 3.4)
FetchContent_Declare(glm      GIT_REPOSITORY https://github.com/g-truc/glm.git          GIT_TAG 1.0.1)
FetchContent_Declare(glew     GIT_REPOSITORY https://github.com/Perlmint/glew-cmake.git GIT_TAG glew-cmake-2.2.0)
FetchContent_Declare(pybind11 GIT_REPOSITORY https://github.com/pybind/pybind11.git     GIT_TAG v2.13.6)
FetchContent_MakeAvailable(glfw glm glew pybind11)

file(GLOB_RECURSE ENGINE_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/input/*.cpp
    ${CMAKE_SOURCE_DIR}/render/*.cpp
    ${CMAKE_SOURCE_DIR}/engine/*.cpp)

# skip an old test file in render/ if it is still there (it has its own main())
list(FILTER ENGINE_SOURCES EXCLUDE REGEX ".*/render/main\\.cpp$")

pybind11_add_module(engine ${ENGINE_SOURCES})

target_include_directories(engine PRIVATE ${CMAKE_SOURCE_DIR})
target_compile_definitions(engine PRIVATE GLEW_STATIC)
target_link_libraries(engine PRIVATE glfw glm::glm libglew_static)

if(MINGW)
    target_link_options(engine PRIVATE -static-libgcc -static-libstdc++)
    # To run on a PC without CLion, also bundle libwinpthread by uncommenting:
    # target_link_options(engine PRIVATE -static)
endif()

# put engine.pyd next to main.py
set_target_properties(engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR})
