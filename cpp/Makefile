INCLUDES = -I.
OBJ = var.o codec.o int_codec.o string_codec.o array_codec.o type_codec.o any_codec.o null_codec.o bool_codec.o float_codec.o time_codec.o dict_codec.o tuple_codec.o struct_codec.o
TEST_SRCS = var_test.cpp int_codec_test.cpp string_codec_test.cpp array_codec_test.cpp type_codec_test.cpp any_codec_test.cpp null_codec_test.cpp bool_codec_test.cpp float_codec_test.cpp time_codec_test.cpp dict_codec_test.cpp tuple_codec_test.cpp struct_codec_test.cpp
VPATH = .:build:serializer

# If your boost installation / compiler version has trouble compiling
# var.h, try setting CFLAGS via an environment variable as below.
# CFLAGS = -DBOOST_VARIANT_NO_FULL_RECURSIVE_VARIANT_SUPPORT

all: build demo

build/%.o: %.cpp
	$(CXX) -g -Wall -c $(CFLAGS) $(INCLUDES) -o $@ $<

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

# PROGRAMS - END

depend:
	find_deps > deps.txt

-include deps.txt
