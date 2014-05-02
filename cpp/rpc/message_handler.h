#ifndef MESSAGE_HANDLER_HGUARD_
#define MESSAGE_HANDLER_HGUARD_

#include <string>

namespace serf {

    class MessageRouter;

    class MessageHandler
    {
    public:
        MessageHandler(MessageRouter* router=NULL);

        void setRouter(MessageRouter* router);

        void offline(std::string const& node, int code);
        void handle(std::string const& node, std::string const& msg);
    private:
        MessageRouter* router_; // not owned.
    };
}

#endif // MESSAGE_HANDLER_HGUARD_
