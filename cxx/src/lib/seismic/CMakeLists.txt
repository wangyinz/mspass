FILE(GLOB sources_seismic *.cc)
include_directories(
  ${Boost_INCLUDE_DIRS}
  ${pybind11_INCLUDE_DIR}
  ${PYTHON_INCLUDE_DIRS}
  ${PROJECT_BINARY_DIR}/include
  ${PROJECT_SOURCE_DIR}/include)

add_library(seismic STATIC ${sources_seismic})
target_link_libraries(seismic PRIVATE utility ${BLAS_LIBRARIES} ${LAPACK_LIBRARIES})

install (TARGETS seismic DESTINATION lib)
