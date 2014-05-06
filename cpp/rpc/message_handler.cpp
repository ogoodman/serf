#include <serf/rpc/message_handler.h>

#include <sstream>
#include <serf/serializer/any_codec.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/var_callable_example.h>
#include <serf/debug.h>

namespace serf {

    class VarReplyCallback : public Callback<Var> {
    public:
        VarReplyCallback(MessageRouter* router, std::string const& node, std::string const& addr) :
            router_(router), node_(node), addr_(addr) {}

        virtual void call(Result<Var>::Ptr result);
    private:
        MessageRouter* router_; // not owned.
        std::string node_;
        std::string addr_;
    };

    void VarReplyCallback::call(Result<Var>::Ptr result) {
        AnyCodec codec;
        Context ctx;
        std::map<std::string, Var> reply_m;

        try {
            reply_m["r"] = result.get();
        } catch (std::exception& e) {
            // FIXME: we're supposed to send a Record, but we haven't
            // defined them yet.
            std::vector<Var> exc;
            exc.push_back(std::string("UnknownException"));
            std::vector<Var> exc_args;
            exc_args.push_back(std::string(e.what()));
            exc.push_back(exc_args);
            reply_m["e"] = exc;
        }

        std::ostringstream out;
        codec.encode(out, addr_, ctx);
        codec.encode(out, Var(reply_m), ctx);

        router_->send(node_, out.str());
    }

    MessageHandler::MessageHandler(MessageRouter* router)
        : router_(router), servant_(new ExampleImpl) {}

    MessageHandler::~MessageHandler() {
        delete servant_;
    }

    void MessageHandler::handle(std::string const& node, std::string const& msg) {
        std::istringstream in(msg);
        AnyCodec codec;
        Context ctx;
        Var addr; codec.decode(in, addr, ctx);
        Var call; codec.decode(in, call, ctx);

        std::string method = boost::get<std::string>(M(call)["m"]);

        // This should match the node above since both come from
        // what the caller says he is. So doesn't that make it a bit
        // redundant?
        // std::string reply_node = boost::get<std::string>(M(call)["N"]);
        std::string reply_addr = boost::get<std::string>(M(call)["O"]);
        Var args = M(call)["a"];

        servant_->varCall_a_(method, V(args))->then(
            new VarReplyCallback(router_, node, reply_addr));
    }

    void MessageHandler::offline(std::string const& node, int code) {
        SAY(node << " went offline with code = " << code);
    }

    void MessageHandler::setRouter(MessageRouter* router) {
        router_ = router;
    }

}
