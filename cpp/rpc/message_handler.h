#ifndef MESSAGE_HANDLER_HGUARD_
#define MESSAGE_HANDLER_HGUARD_

#include <string>

namespace serf {

    /** \brief Processor for inbound messages from a MessageRouter.
     */
    class MessageHandler
    {
    public:
        ~MessageHandler();

        /** \brief Called when a node is found to be unreachable.
         */
        virtual void offline(std::string const& node, int code) = 0;

        /** \brief Called when a message arrives.
         */
        virtual void handle(std::string const& node, std::string const& msg) = 0;
    };
}

#endif // MESSAGE_HANDLER_HGUARD_
