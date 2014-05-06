#include <serf/rpc/var_proxy.h>

#include <serf/rpc/var_caller.h>

namespace serf {

    VarProxy::VarProxy(VarCaller* remote, std::string const& node, std::string const& addr)
        : remote_(remote), node_(node), addr_(addr) {}

    Var VarProxy::varCall_(std::string const& method, std::vector<Var> const& args) {
        throw std::runtime_error("not implemented: proxy not synchronous");
    }        

    FVarP VarProxy::varCall_a_(std::string const& method, std::vector<Var> const& args) {
        std::map<std::string, Var> call_m;
        call_m["o"] = addr_;
        call_m["m"] = method;
        call_m["a"] = args;
        return remote_->callRemote(node_, call_m);
    }

    void VarProxy::varDecodeExc_(Var const& exc) {
        // exc should be [exc-type, [args...]].
        std::string what(boost::get<std::string>(V(V(exc)[1])[0]));
        throw std::runtime_error(what);
    }
}
