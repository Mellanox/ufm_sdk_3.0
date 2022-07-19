all: libservice_record.so service_record_test libservice_record_wrapper.so service_record_wrapper_test

libservice_record.so:
	gcc -g -fPIC -O2 -DNDEBUG  -fPIC -shared -Wl,-soname,libservice_record.so -o libservice_record.so -DCLX_LOG_LEVEL=7 \
         -Dservice_record_EXPORTS -Isrc -I../../src -I/usr/include/infiniband -O2 -DNDEBUG -fPIC \
         -Wall -Wstrict-prototypes -fno-strict-aliasing -std=gnu99 sr.c services.c ../common/logger.c -libmad -libumad

service_record_test:
	gcc -g -o service_record_test -DCLX_LOG_LEVEL=7 -I../../src -I/tmp/Collectx/src -I/usr/include/infiniband -O2 -DNDEBUG\
        -Wall -Wstrict-prototypes -fno-strict-aliasing -std=gnu99 -Wl,-rpath,. ./sr_test.c  -lservice_record -L.

clean:
	rm -rf libservice_record.so service_record_test libservice_record_wrapper.so service_record_wrapper_test

run_server: service_record_test
	./service_record_test 1

run_client: service_record_test
	./service_record_test 0
        
libservice_record_wrapper.so:
	gcc -g -fPIC -O2 -DNDEBUG  -fPIC -shared -Wl,-soname,libservice_record_wrapper.so -o libservice_record_wrapper.so -DCLX_LOG_LEVEL=7 \
         -Dservice_record_EXPORTS -Isrc -I../../src -I/usr/include/infiniband -O2 -DNDEBUG -fPIC \
         -Wall -Wstrict-prototypes -fno-strict-aliasing -std=gnu99 sr.c services.c sr_wrapper.c ../common/logger.c -libmad -libumad

service_record_wrapper_test:
	gcc -g -o service_record_wrapper_test -DCLX_LOG_LEVEL=7 -I../../src -I/tmp/Collectx/src -I/usr/include/infiniband -O2 -DNDEBUG\
        -Wall -Wstrict-prototypes -fno-strict-aliasing -std=gnu99 -Wl,-rpath,. ./sr_wrapper_test.c  -lservice_record_wrapper -L.
