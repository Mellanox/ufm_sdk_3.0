#
# Copyright (C) Mellanox Technologies Ltd. 2017.  ALL RIGHTS RESERVED.
#
# See file LICENSE for terms.
#
set (service_record_sources
        sr.c
        sr.h
        services.c
        services.h
)

set (service_record_wrapper_sources
        ${service_record_sources}
        sr_wrapper.c
        sr_wrapper.h
)

set (service_record_all_sources
        ${service_record_sources}
        sr_test.c
        sr_wrapper_test.c)

check_coding_style (service_record ${service_record_all_sources})

add_compile_options (-Wstrict-prototypes)
add_compile_options (-fno-strict-aliasing)
add_link_options (-fPIC)

set (CMAKE_C_STANDARD 99)
set (CMAKE_CXX_STANDARD 11)

# Counters service_record shared library
add_library (service_record STATIC ${service_record_sources})
target_include_directories(service_record PUBLIC "/usr/include/infiniband/")
target_link_libraries (service_record LINK_PUBLIC ibumad)
set_target_properties (service_record PROPERTIES LINKER_LANGUAGE C)

# Counters service_record shared library
add_library (service_record_wrapper SHARED ${service_record_wrapper_sources})
target_include_directories(service_record_wrapper PUBLIC "/usr/include/infiniband/")
target_link_libraries (service_record_wrapper LINK_PUBLIC ibumad)
set_target_properties (service_record_wrapper PROPERTIES LINKER_LANGUAGE C)

add_executable (service_record_test sr_test.c)
target_link_libraries (service_record_test LINK_PUBLIC service_record clx_common)

add_executable (service_record_wrapper_test sr_wrapper_test.c)
target_link_libraries (service_record_wrapper_test LINK_PUBLIC service_record_wrapper clx_common)

install (TARGETS service_record service_record_wrapper COMPONENT collectx DESTINATION lib)
