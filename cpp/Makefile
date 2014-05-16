INCLUDES = -I.

UTIL_OBJ = runnable.o debug.o

SERIALIZER_OBJ = var.o codec.o int_codec.o string_codec.o array_codec.o type_codec.o any_codec.o null_codec.o bool_codec.o float_codec.o time_codec.o dict_codec.o tuple_codec.o struct_codec.o record.o record_codec.o

REACTOR_OBJ = accept_reader.o data_handler.o data_reader.o line_handler.o reactor.o reader.o connect_reader.o task.o system_clock.o

RPC_OBJ = connection.o connection_factory.o message_handler.o message_router.o var_callable.o example.o var_caller.o var_proxy.o rpc_handler.o serf_exception.o example_gen.o

OBJ = $(UTIL_OBJ) $(SERIALIZER_OBJ) $(REACTOR_OBJ) $(RPC_OBJ)

TEST_SRCS = var_test.cpp int_codec_test.cpp string_codec_test.cpp array_codec_test.cpp type_codec_test.cpp any_codec_test.cpp null_codec_test.cpp bool_codec_test.cpp float_codec_test.cpp time_codec_test.cpp dict_codec_test.cpp tuple_codec_test.cpp struct_codec_test.cpp accept_reader_test.cpp data_handler_test.cpp data_reader_test.cpp line_handler_test.cpp reactor_test.cpp reader_test.cpp connect_reader_test.cpp connection_test.cpp connection_factory_test.cpp message_router_test.cpp task_test.cpp system_clock_test.cpp var_callable_test.cpp future_test.cpp var_proxy_test.cpp rpc_handler_test.cpp extract_test.cpp serf_exception_test.cpp record_test.cpp on_load_test.cpp

VPATH = .:build:util:serializer:reactor:rpc

# If your boost installation / compiler version has trouble compiling
# var.h, try setting CFLAGS via an environment variable as below.
# CFLAGS = -DBOOST_VARIANT_NO_FULL_RECURSIVE_VARIANT_SUPPORT

all: build demo

build/%.o: %.cpp
	$(CXX) -g -Wall -c $(CFLAGS) $(INCLUDES) -o $@ $<

rpc/example_gen.cpp: example.idl
	../scripts/idl_to_cpp.py example.idl rpc

rpc/example_gen.h: example.idl
	../scripts/idl_to_cpp.py example.idl rpc

build/example.o: rpc/example_gen.h

build/test_runner.cpp: $(TEST_SRCS)
	cxxtestgen --error-printer -o $@ $^

test_runner: $(OBJ:%=build/%) build/test_runner.o
	$(CXX) $(CFLAGS) $(INCLUDES) $(LIBS) -o $@ $^

test: build test_runner
	./test_runner

build:
	mkdir -p build

clean:
	rm -rf build

# PROGRAMS
demo: $(OBJ:%=build/%) build/demo.o
	$(CXX) $(LIBS) -o $@ $^

server: $(REACTOR_OBJ:%=build/%) build/server.o
	g++ $(LIBS) -o $@ $^

timeout: $(REACTOR_OBJ:%=build/%) build/timeout.o
	g++ $(LIBS) -o $@ $^

serf_server: $(OBJ:%=build/%) build/serf_server.o
	g++ $(LIBS) -o $@ $^
# PROGRAMS - END

depend:
	find_deps > deps.txt

-include deps.txt
