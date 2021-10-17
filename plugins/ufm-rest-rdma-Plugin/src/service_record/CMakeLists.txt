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

check_coding_style (service_record ${service_record_sources})

add_compile_options (-Wstrict-prototypes)
add_compile_options (-fno-strict-aliasing) 
add_link_options (-fPIC)

set (CMAKE_C_STANDARD 99)
set (CMAKE_CXX_STANDARD 11)

# Counters collector shared library 
add_library (service_record SHARED ${service_record_sources})
target_include_directories(service_record PUBLIC "/usr/include/infiniband/")
target_link_libraries (service_record LINK_PUBLIC ibumad)
set_target_properties (service_record PROPERTIES LINKER_LANGUAGE C)

install (TARGETS service_record COMPONENT collectx LIBRARY DESTINATION lib)

add_executable (service_record_test sr_test.c)
target_link_libraries (service_record_test LINK_PUBLIC service_record clx_common)
