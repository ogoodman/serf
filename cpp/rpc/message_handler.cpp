#include <serf/rpc/message_handler.h>

#include <serf/rpc/message_router.h>
#include <serf/debug.h>

namespace serf {

    MessageHandler::MessageHandler(MessageRouter* router) : router_(router) {}

    void MessageHandler::handle(std::string const& node, std::string const& msg) {
        SAY(node << " sent " << repr(msg));

        if (msg == "send") {
            if (router_) {
                router_->send("127.0.0.1:6669", "Hello!");
            } else {
                SAY("No router, can't send");
            }
        }
    }

    void MessageHandler::offline(std::string const& node, int code) {
        SAY(node << " went offline with code = " << code);
    }

    void MessageHandler::setRouter(MessageRouter* router) {
        router_ = router;
    }

}
