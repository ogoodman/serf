#include <serf/rpc/rpc_handler.h>

#include <sstream>
#include <stdlib.h>
#include <serf/serializer/any_codec.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/var_callable_example.h>
#include <serf/debug.h>

namespace serf {

    static const char ALPHANUM[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    std::string randomString(size_t len) {
        static bool initialized = false;
        if (!initialized) {
            srandomdev();
            initialized = true;
        }
        std::string s(len, '\0');
        for (size_t i = 0; i < len; ++i) {
            s[i] = ALPHANUM[random() % (sizeof(ALPHANUM) - 1)];
        }
        return s;
    }

    /** \brief Part of RPCHandler.
     *
     * Takes the response from a call on a servant (VarCallable) and
     * sends it back to the node that made the call.
     */
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

    RPCHandler::RPCHandler(MessageRouter* router)
        : router_(router) {
        ExampleImpl* servant = new ExampleImpl();
        servant_ = servant;
        servant->proxy.reset(
            new ExamplePrx(this, "127.0.0.1:6502", "QRJSY2M9RA0H"));
    }

    RPCHandler::~RPCHandler() {
        delete servant_;
    }

    void RPCHandler::handle(std::string const& node, std::string const& msg) {
        std::istringstream in(msg);
        AnyCodec codec;
        Context ctx;

        Var addr; codec.decode(in, addr, ctx);

        // FIXME: this will throw if someone sends us an exception since we
        // don't know how to deal with Records yet.
        Var call; codec.decode(in, call, ctx);

        std::string addr_s(boost::get<std::string const&>(addr));

        std::map<std::string, Var>& call_m(M(call));
        std::map<std::string, Var>::iterator pos = call_m.find("m");

        if (pos == call_m.end()) {
            // It should be a reply. 
            // FIXME: this is not a good way to decide.
            Future<Var>::Ptr cb = callbacks_[addr_s];
            if (!cb) {
                SAY("received a return value for a call we never sent");
                return;
            }
            callbacks_.erase(addr_s);
            // This will cause the Resolver in var_proxy.h to run which
            // will create a ProxyCallResult (also in var_proxy.h).
            // That will probably be consumed right away and have its
            // get() method called. 
            cb->resolve(call);
            return;
        }

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

    void VarReplyCallback::call(Result<Var>::Ptr result) {
        AnyCodec codec;
        Context ctx;
        std::map<std::string, Var> reply_m;

        try {
            reply_m["r"] = result->get();
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

    void RPCHandler::offline(std::string const& node, int code) {
        SAY(node << " went offline with code = " << code);
    }

    void RPCHandler::setRouter(MessageRouter* router) {
        router_ = router;
    }

    Future<Var>::Ptr RPCHandler::callRemote(std::string const& node, Var& call) {
        Future<Var>::Ptr reply(new Future<Var>);
        std::string reply_addr = randomString(12);
        std::ostringstream out;
        M(call)["O"] = reply_addr;
        M(call)["N"] = std::string("127.0.0.1:6504"); // FIXME.
        AnyCodec codec;
        Context ctx;
        codec.encode(out, M(call)["o"], ctx);
        codec.encode(out, call, ctx);
        router_->send(node, out.str());
        callbacks_[reply_addr] = reply;
        return reply;
    }

}
