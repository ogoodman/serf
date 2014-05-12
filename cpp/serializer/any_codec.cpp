#include <serf/serializer/any_codec.h>

#include <serf/serializer/null_codec.h>
#include <serf/serializer/bool_codec.h>
#include <serf/serializer/int_codec.h>
#include <serf/serializer/time_codec.h>
#include <serf/serializer/float_codec.h>
#include <serf/serializer/type_codec.h>
#include <serf/serializer/array_codec.h>
#include <serf/serializer/dict_codec.h>
#include <serf/serializer/string_codec.h>

using namespace std;
using namespace boost;

namespace serf {

    class AnyEncoder : public static_visitor<void>
    {
    public:
        AnyEncoder(ostream& out, Context& ctx) : out_(&out), ctx_(&ctx) {}
    
        void operator() (blank value) const;
        void operator() (bool value) const;
        void operator() (byte value) const;
        void operator() (int32_t value) const;
        void operator() (int64_t value) const;
        void operator() (double value) const;
        void operator() (boost::posix_time::ptime value) const;
        void operator() (string const& value) const;
        void operator() (vector<Var> const& value) const;
        void operator() (map<string,Var> const& value) const;
        void operator() (CodecP value) const;
        void operator() (Record const& value) const;
    
    private:
        ostream* out_;
        Context* ctx_;
    };
    
    void AnyEncoder::operator() (blank value) const {
        NullCodec nc;
        nc.encodeType(*out_);
    }
    
    void AnyEncoder::operator() (bool value) const {
        BoolCodec bc;
        bc.encodeType(*out_);
        bc.encode(*out_, value);
    }
    
    void AnyEncoder::operator() (byte value) const {
        IntCodec bc(1, false);
        bc.encodeType(*out_);
        bc.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (int32_t value) const {
        IntCodec IC;
        IC.encodeType(*out_);
        IC.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (int64_t value) const {
        IntCodec IC(8);
        IC.encodeType(*out_);
        IC.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (double value) const {
        FloatCodec fc;
        fc.encodeType(*out_);
        fc.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (boost::posix_time::ptime value) const {
        TimeCodec tc;
        tc.encodeType(*out_);
        tc.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (string const& value) const {
        char type_byte = isAscii(value) ? 'a' : 'r';
        StringCodec SC(type_byte);
        SC.encodeType(*out_);
        SC.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (vector<Var> const& value) const {
        CodecP ac(new AnyCodec());
        ArrayCodec LC(ac);
        LC.encodeType(*out_);
        LC.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (map<string,Var> const& value) const {
        CodecP sc(new StringCodec('k'));
        CodecP ac(new AnyCodec());
        DictCodec dc(sc, ac);
        dc.encodeType(*out_);
        dc.encode(*out_, value, *ctx_);
    }
    
    void AnyEncoder::operator() (CodecP value) const {
        value->encodeType(*out_);
    }

    void AnyEncoder::operator() (Record const& value) const {
        IntCodec ic;
        StringCodec data('r');
        if (value.type_name == "@") {
            (*out_) << '@';
            ic.encode(*out_, value.type_id);
            data.encode(*out_, value.value, *ctx_);
            return;
        }
        int type_id;
        CodecP codec = ctx_->namedCodec(value.type_name, type_id);
        if (codec) {
            (*out_) << '@';
            ic.encode(*out_, type_id);
            std::ostringstream tmp;
            codec->encode(tmp, value.value, *ctx_);
            data.encode(*out_, tmp.str());
        } else {
            StringCodec token('k');
            AnyCodec ac;
            (*out_) << 'R';
            token.encode(*out_, value.type_name);
            ac.encode(*out_, value.value, *ctx_);
        }
    }
    
    std::string AnyCodec::typeName() {
        return "ANY";
    }
    void AnyCodec::encodeType(ostream& out) {
        out << 'A';
    }
    void AnyCodec::encode(ostream& out, Var const& value, Context& ctx) {
        apply_visitor(AnyEncoder(out, ctx), value);
    }
    void AnyCodec::decode(istream& in, Var& value, Context& ctx) {
        TypeCodec tc;
        CodecP c = tc.decode(in, ctx);
        c->decode(in, value, ctx);
    }
    
    CodecP AnyCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new AnyCodec());
    }
    char AnyCodec::Factory::typeByte() const {
        return 'A';
    }
}
