#include <serf/rpc/message_handler.h>

#include <sstream>
#include <serf/serializer/any_codec.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/var_callable_example.h>
#include <serf/debug.h>

namespace serf {

    MessageHandler::MessageHandler(MessageRouter* router)
        : router_(router), servant_(new ExampleImpl) {}

    MessageHandler::~MessageHandler() {
        delete servant_;
    }

    void MessageHandler::handle(std::string const& node, std::string const& msg) {
        SAY(node << " sent " << repr(msg));

        std::istringstream in(msg);
        AnyCodec codec;
        Context ctx;
        Var addr; codec.decode(in, addr, ctx);
        Var call; codec.decode(in, call, ctx);
        SHOW(addr);
        SHOW(call);

        std::string method = boost::get<std::string>(M(call)["m"]);

        // This should match the node above since both come from
        // what the caller says he is. So doesn't that make it a bit
        // redundant?
        std::string reply_node = boost::get<std::string>(M(call)["N"]);
        Var args = M(call)["a"];

        std::map<std::string, Var> reply_m;
        reply_m["r"] = servant_->varCall_(method, V(args));

        std::ostringstream out;
        codec.encode(out, M(call)["O"], ctx); // Reply addr (object)
        codec.encode(out, Var(reply_m), ctx);

        router_->send(node, out.str());

        /*
        if (msg == "send") {
            if (router_) {
                router_->send("127.0.0.1:6669", "Hello!");
            } else {
                SAY("No router, can't send");
            }
        }
        */
    }

    void MessageHandler::offline(std::string const& node, int code) {
        SAY(node << " went offline with code = " << code);
    }

    void MessageHandler::setRouter(MessageRouter* router) {
        router_ = router;
    }

}
