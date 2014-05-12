#include <iostream>
#include <map>
#include <string>
#include <vector>
#include <serf/serializer/var.h>
#include <serf/serializer/int_codec.h>
#include <serf/serializer/any_codec.h>
#include <serf/serializer/time_codec.h>
#include <serf/serializer/type_codec.h>

#include <serf/util/debug.h>

using namespace std;
using namespace boost;
using namespace boost::posix_time;
using namespace boost::gregorian;
using namespace serf;

int main(int argc, char* argv[])
{
    SAY("The null type");
    Var bv;
    get<blank>(bv);
    SHOW(bv);

    IntCodec ic;
    AnyCodec ac;

    SAY("Int encoding");
    Var i(42);
    SHOW(i);
    SHOW(repr(ic.encodes(i)));
    SHOW(repr(ac.encodes(i)));

    SAY("A negative int");
    Var answer = ic.decodes("\xff\xff\xff\xff");
    SHOW(get<int>(answer));

    SAY("A time");
    ptime lb(date(2005,12,8), time_duration(10,17,0));

    SAY("Nested lists");
    vector<Var> sub;
    sub.push_back(-1);
    sub.push_back(string("hi"));
    sub.push_back(true);
    sub.push_back(byte('X'));

    vector<Var> vv;
    vv.push_back(1);
    vv.push_back(4);
    vv.push_back(sub);
    vv.push_back(2.718);
    vv.push_back(blank());
    vv.push_back(lb);
    Var v1(vv);

    SHOW(v1);
    string ev = ac.encodes(v1);
    SHOW(repr(ev));
    Var v2 = ac.decodes(ev);
    SHOW(v2);

    SAY("Dictionaries");
    TypeCodec typ;
    map<string, Var> sd;
    sd["name"] = string("Fred");
    sd["age"] = 42;
    sd["male"] = true;
    sd["dob"] = ptime(date(1965,Jul,18), time_duration(1,23,45));
    Var d1(sd);
    SHOW(d1);

    string ed = ac.encodes(d1);
    SHOW(repr(ed));
    Var d2(ac.decodes(ed));
    SHOW(d2);

    SHOW(typ.decodes(ed));

    TimeCodec tc;
    SHOW(repr(tc.encodes(sd["dob"])));

    SHOW(tc.typeName());

    SAY("Tuple");
    CodecP tupc(get<CodecP>(typ.decodes(string("T\0\0\0\4iubB", 9))));
    SHOW(tupc->typeName());
    Var tval1(sub); // sub has right types for this tuple.
    string te(tupc->encodes(tval1));
    SHOW(tval1);
    SHOW(repr(te));
    Var tval2(tupc->decodes(te));
    SHOW(tval2);

    SAY("Struct");
    // The type of structs (in general) is a sequence of (key, type) pairs.
    string meta(string("LT\0\0\0\x02kY", 8));
    SHOW(typ.decodes(meta));
    CodecP metac(get<CodecP>(typ.decodes(meta)));
    // Here is a particular struct.
    vector<Var> f0, f1, sdef;
    f0.push_back(string("name"));
    f0.push_back(typ.decodes("u")); // TEXT codec
    f1.push_back(string("age"));
    f1.push_back(typ.decodes("h")); // INT16 codec
    sdef.push_back(f0);
    sdef.push_back(f1);
    SHOW(sdef);
    string sdef_e(metac->encodes(sdef));
    SHOW(repr(sdef_e));

    return 0;
}
