#include <serf/rpc/var_proxy.h>

#include <serf/rpc/var_caller.h>
#include <serf/rpc/serf_exception.h>
#include <serf/util/debug.h>

namespace serf {

    VarProxy::VarProxy(VarCaller* remote, std::string const& node, std::string const& addr)
        : remote_(remote), node_(node), addr_(addr) {}

    VarProxy::VarProxy(VarCaller* remote, Record const& addr)
        : remote_(remote),
          node_(boost::get<std::string const&>(M(addr.value).at("node"))),
          addr_(boost::get<std::string const&>(M(addr.value).at("path"))) {
        if (addr.type_name != "ref") {
            throw TypeError("type: \"" + addr.type_name + "\" is not a proxy");
        }
    }

    FVarP VarProxy::call_(std::string const& method, std::vector<Var> const& args) {
        std::map<std::string, Var> call_m;
        call_m["o"] = addr_;
        call_m["m"] = method;
        call_m["a"] = args;
        Var call(call_m);
        return remote_->callRemote(node_, call);
    }

    void VarProxy::throw_(Var const& exc) {
        Exceptions::throw_(V(exc));
    }

    VarProxy::operator Record() const {
        std::map<std::string, Var> rec_m;
        rec_m["node"] = node_;
        rec_m["path"] = addr_;
        return Record("ref", rec_m);
    }
}
