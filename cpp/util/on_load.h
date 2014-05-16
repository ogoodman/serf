#ifndef ON_LOAD_HGUARD_
#define ON_LOAD_HGUARD_

namespace serf {

    typedef void (*voidfun)();

    /** \brief Helper for calling functions at scope entry and exit.
     */
    class OnLoad
    {
    public:
        OnLoad(voidfun before, voidfun after=NULL) : after_(after) {
            if (before) before();
        }
        ~OnLoad() {
            if (after_) after_();
        }

    private:
        voidfun after_;
    };
}

#endif // ON_LOAD_HGUARD_
