#!/usr/bin/python3
#-*- coding: utf-8 -*-
import ctypes 
import sys
#ctypes.cdll.LoadLibrary('/opt/ufm/opensm/lib/libibmad.so')
#ctypes.cdll.LoadLibrary('/opt/ufm/opensm/lib/libibumad.so')
#ib_mad_lib = ctypes.CDLL('/opt/ufm/opensm/lib/libibmad.so')
#ib_umad_lib = ctypes.CDLL('/opt/ufm/opensm/lib/libibumad.so')
sr_test = ctypes.CDLL('./libservice_record_wrapper.so')
print (sr_test)
# # Function returns int
# sr_test.service_record_init.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_init.argtypes = [ctypes.c_int, ]
# # Function returns int
# sr_test.service_record_register_service.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_register_service.argtypes = []
# # Function returns int
# sr_test.service_record_register_service.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_register_service.argtypes = []
# # Function returns int
# sr_test.service_record_unregister_service.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_unregister_service.argtypes = []
# # Function returns int
# sr_test.service_record_query_service.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_query_service.argtypes = []
# # Function returns int
# sr_test.service_record_cleanup.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_cleanup.argtypes = []
# # Function returns int
# sr_test.service_record_printout_service.restype = ctypes.c_int
# # Function gets argument int
# sr_test.service_record_printout_service.argtypes = []

def main():
    '''
    
    '''
if __name__ == '__main__':
    main()
