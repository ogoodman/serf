#include <serf/serializer/record.h>
#include <cxxtest/TestSuite.h>

#include <iostream>
#include <serf/serializer/any_codec.h>

using namespace serf;

class TestContext : public Context
{
public:
    CodecP codec(int type_id, std::string& type_name) {
        if (type_id == 14) {
            type_name = "fred";
            return CodecP(new IntCodec(2, false)); // uint16.
        }
        type_id = 0;
        return CodecP();
    }
    CodecP namedCodec(std::string const& type_name, int& type_id) {
        if (type_name == "fred") {
            type_id = 14;
            return CodecP(new IntCodec(2, false)); // uint16.
        }
        return CodecP();
    }
};

class RecordTest : public CxxTest::TestSuite
{
public:
    void testRecord() {
        AnyCodec ac;
        Context ctx;
        std::ostringstream out;
        Record fred("fred", 42);

        // Encoding with the default context yields a record.
        ac.encode(out, fred, ctx);
        std::string enc_rec("R\x00\x04""fredi\x00\x00\x00*", 12);
        TS_ASSERT_EQUALS(out.str(), enc_rec);

        // Decoding the record yields the original Record.
        Var dec;
        std::istringstream in(enc_rec);
        ac.decode(in, dec, ctx);
        TS_ASSERT_EQUALS(dec, Var(fred));

        // Encoding with a context that knows the name yields a message.
        out.str("");
        TestContext tctx;
        std::string enc_msg("@\x00\x00\x00\x0E\x00\x00\x00\x02\x00*", 11);
        ac.encode(out, fred, tctx);
        TS_ASSERT_EQUALS(out.str(), enc_msg);

        // Using the same context to decode gives the original Record.
        // Actually the type_id and codec are set in dec but not in fred
        // but they are ignored in comparisons and not used in encoding.
        dec = Var();
        in.str(enc_msg);
        ac.decode(in, dec, tctx);
        TS_ASSERT_EQUALS(dec, Var(fred));

        // Decoding a message using a context that knows nothing
        // gives a Record with a type_name of "@". The body is just
        // the raw data and the type_id is retained.
        dec = Var();
        in.str(enc_msg);
        ac.decode(in, dec, ctx);
        Record dec_r(boost::get<Record>(dec));
        TS_ASSERT_EQUALS(dec_r, Record("@", std::string("\0*", 2), 14));

        // Re-encoding a message that was decoded without a context
        // that knows about it returns the original data.
        out.str("");
        ac.encode(out, dec, ctx);
        TS_ASSERT_EQUALS(out.str(), enc_msg);
    }
};
