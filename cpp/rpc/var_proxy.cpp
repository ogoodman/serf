#include <serf/rpc/var_proxy.h>

#include <serf/rpc/var_caller.h>
#include <serf/debug.h>

namespace serf {

    VarProxy::VarProxy(VarCaller* remote, std::string const& node, std::string const& addr)
        : remote_(remote), node_(node), addr_(addr) {}

    FVarP VarProxy::remoteCall_a_(std::string const& method, std::vector<Var> const& args) {
        std::map<std::string, Var> call_m;
        call_m["o"] = addr_;
        call_m["m"] = method;
        call_m["a"] = args;
        Var call(call_m);
        return remote_->callRemote(node_, call);
    }

    void VarProxy::varDecodeExc_(Var const& exc) {
        // exc should be [exc-type, args...].
        std::string what(boost::get<std::string>(V(exc)[1]));
        throw std::runtime_error(what);
    }
}
