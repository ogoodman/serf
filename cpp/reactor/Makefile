OBJ = reactor.o accept_reader.o data_reader.o line_handler.o
INCLUDES = -I.

TEST_SRCS = reactor_test.cpp

all: server

build/%.o: %.cpp
	g++ -g -Wall -c $(INCLUDES) -o $@ $<

server: $(OBJ:%=build/%) build/server.o
	g++ $(LIBS) -o $@ $^

build/test_runner.cpp: $(TEST_SRCS)
	cxxtestgen.pl --error-printer -o $@ $^

test_runner: $(OBJ:%=build/%) build/test_runner.cpp
	g++ -I. $(INCLUDES) $(LIBS) -o $@ $^

test: build test_runner
	./test_runner
