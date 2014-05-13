#include <serf/rpc/rpc_handler.h>

#include <sstream>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <serf/serializer/any_codec.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/var_callable.h>
#include <serf/rpc/serf_exception.h>
#include <serf/util/debug.h>

namespace serf {

    static const char ALPHANUM[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    std::string randomString(size_t len) {
        static bool initialized = false;
        if (!initialized) {
#ifdef NO_SRANDOMDEV
            int fd = open("/dev/urandom", O_RDONLY);
            unsigned int seed;
            if (read(fd, (void*)&seed, sizeof(seed)) != sizeof(seed)) throw std::runtime_error("failed to seed random()");
            close(fd);
            srandom(seed);
#else
            srandomdev();
#endif
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
    }

    RPCHandler::~RPCHandler() {
        std::map<std::string, VarCallable*>::iterator it, e = servants_.end();
        for (it = servants_.begin(); it != e; ++it) {
            delete it->second;
        }
    }

    /** \brief Handle a call or return value from another node.
     */
    void RPCHandler::handle(std::string const& node, std::string const& msg) {
        std::istringstream in(msg);
        AnyCodec codec;
        Context ctx;

        Var call; codec.decode(in, call, ctx);

        std::map<std::string, Var>& call_m(M(call));

        std::string addr(boost::get<std::string const&>(call_m["o"]));

        std::map<std::string, Var>::iterator pos = call_m.find("m");

        if (pos == call_m.end()) {
            // It should be a reply. 
            // FIXME: this is not a great way to decide.
            std::string cb_id = node + '/' + addr;
            Future<Var>::Ptr cb = callbacks_[cb_id];
            if (!cb) {
                SAY("received a return value for a call we never sent");
                return;
            }
            callbacks_.erase(cb_id);
            // This will cause the Resolver in var_proxy.h to run which
            // will create a ProxyCallResult (also in var_proxy.h).
            // That will probably be consumed right away and have its
            // get() method called. 
            cb->resolve(call);
            return;
        }

        std::string method(boost::get<std::string const&>(pos->second));
        std::string reply_addr = boost::get<std::string>(M(call)["O"]);
        std::string object_id = boost::get<std::string>(M(call)["o"]);
        Var args = M(call)["a"];

        VarCallable* servant = servants_[object_id];
        if (!servant) {
            std::vector<Var> exc(2);
            exc[0] = std::string("NoSuchObject");
            exc[1] = object_id;
            std::map<std::string, Var> reply_m;
            reply_m["e"] = exc;
            reply_m["o"] = reply_addr;
            std::ostringstream out;
            codec.encode(out, Var(reply_m), ctx);
            router_->send(node, out.str());
            return;
        }

        servant->call_(method, V(args), this)->then(
            new VarReplyCallback(router_, node, reply_addr));
    }

    void VarReplyCallback::call(Result<Var>::Ptr result) {
        AnyCodec codec;
        Context ctx;

        Var reply = result->get(); // should be a map, should not throw.
        M(reply)["o"] = addr_;

        std::ostringstream out;
        codec.encode(out, reply, ctx);
        router_->send(node_, out.str());
    }

    /** \brief Handle the node offline event from the MessageRouter.
     *
     * When a node goes offline all pending calls must have their
     * callbacks resolved to a suitable exception. This can happen
     * when a message is sent to a non-existent node or one that is
     * offline because the outgoing message will be accepted for
     * sending before the connection is attempted.
     */
    void RPCHandler::offline(std::string const& node, int code) {
        SAY(node << " offline, code = " << code);
        std::map<std::string, FVarP>::iterator it, e = callbacks_.end();
        for (it = callbacks_.begin(); it != e;) {
            if (it->first.substr(0, node.size()) != node) {
                ++it;
            } else {
                std::map<std::string, Var> exc_m;
                exc_m["e"] = NodeOffline(code).encode();
                it->second->resolve(Var(exc_m));
                callbacks_.erase(it++);
            }
        }
    }

    /** \brief Configure with a MessageRouter if one was not provided
     *  to the constructor.
     */
    void RPCHandler::setRouter(MessageRouter* router) {
        router_ = router;
    }

    /** \brief Make a servant available with the given name.
     */
    void RPCHandler::provide(std::string const& name, VarCallable* servant) {
        delete servants_[name];
        servants_[name] = servant;
    }

    /** \brief For use by VarProxy instances.
     *
     * Makes a remote call. The call argument should be a dictionary
     * with "o" set to the remote object id, "m" set to the method to call
     * and "a" set to a list of arguments.
     *
     * The result should resolve to a dictionary with "r" set to the
     * result or "e" set to an encoded exception.
     */
    Future<Var>::Ptr RPCHandler::callRemote(std::string const& node, Var& call) {
        Future<Var>::Ptr reply(new Future<Var>);
        std::string reply_addr = randomString(12);
        std::ostringstream out;
        M(call)["O"] = reply_addr;
        AnyCodec codec;
        Context ctx;
        codec.encode(out, call, ctx);
        router_->send(node, out.str());
        callbacks_[node + '/' + reply_addr] = reply;
        return reply;
    }

}
