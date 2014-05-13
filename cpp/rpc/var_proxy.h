#ifndef VAR_PROXY_HGUARD_
#define VAR_PROXY_HGUARD_

#include <serf/rpc/var_callable.h>

namespace serf {
    class VarCaller;

    template <typename T>
    class Resolver;

    /** \brief Base class for Proxies.
     *
     * Generated code will call call_ to make remote calls,
     * toFuture<R> to convert return values to the expected type of
     * Future. It may also override throw_ in order to
     * decode and then throw any proxy-specific exception returned
     * from a call.
     */
    class VarProxy
    {
    public:
        VarProxy(VarCaller* remote, std::string const& node, std::string const& addr);
        VarProxy(VarCaller* remote, Record const& addr);

        /** \brief Throws the exception specified by exc.
         */
        virtual void throw_(Var const& exc);

        /** \brief Makes a remote call using the configured VarCaller.
         *
         * The eventual Var result will be a dictionary with either
         * {"r": <result>} or {"e": <encoded-exception>}.
         */
        Future<Var>::Ptr call_(std::string const& method, std::vector<Var> const& args);

    protected:

        /** \brief Converts a Future<Var> into a Future<T>.
         *
         * It sets the callback on the Future<Var> to be a Resolver<T>.
         * When called, this will resolve the Future<T> using a
         * ProxyCallResult<T>. 
         *
         * The Resolver does not call Result<Var>.get()
         * in order to create the ProxyCallResult but
         * rather passes ownership of the Result<Var> to the
         * ProxyCallResult. Result<Var>.get() is called by 
         * ProxyCallResult.get(). This is so that exceptions thrown
         * by Result<Var>.get() or by converting Var to T do not need
         * to be caught and re-packaged for the ProxyCallResult.
         */
        template <typename T>
        typename Future<T>::Ptr toFuture(Future<Var>::Ptr fvp) {
            typename Future<T>::Ptr ftp(new Future<T>());
            fvp->then(new Resolver<T>(this, ftp));
            return ftp;
        }

    private:
        VarCaller* remote_;
        std::string node_;
        std::string addr_;
    };

    /** \brief Part of VarProxy.
     *
     * Holds the Var return value of a Proxy remote call until the
     * callback calls get(). It then attempts to extract the result
     * or throw the exception encoded in the Var return value.
     *
     * In order to decode and throw the correct exception it may
     * need the help of generated code in the Proxy implementation.
     */
    template <typename R>
    class ProxyCallResult : public Result<R>
    {
    public:
        typedef typename add_constref<R>::type ref_type;

        ProxyCallResult(VarProxy* prx, Result<Var>::Ptr result)
            : prx_(prx), result_(result) {}

        virtual ref_type get() const {
            const Var& reply(result_->get()); // {"r": ... } or {"e": ... }
            std::map<std::string, Var> const& reply_m(M(reply));
            std::map<std::string, Var>::const_iterator pos;
            pos = reply_m.find("r");
            if (pos == reply_m.end()) {
                // Should decode and throw the right exception.
                prx_->throw_(reply_m.at("e"));
                throw std::runtime_error("should never get here");
            }
            // FIXME: this won't work for complex pos->second types.
            extract(r_, pos->second);
            return r_;
        }
    private:
        VarProxy* prx_; // not owned
        Result<Var>::Ptr result_;
        mutable R r_;
    };

    /** \brief Part of VarProxy.
     *
     * Specialisation of ProxyCallResult<R> for type Var.
     */
    template <>
    class ProxyCallResult<Var> : public Result<Var>
    {
    public:

        ProxyCallResult(VarProxy* prx, Result<Var>::Ptr result)
            : prx_(prx), result_(result) {
        }

        virtual Var const& get() const {
            const Var& reply(result_->get()); // {"r": ... } or {"e": ... }
            std::map<std::string, Var> const& reply_m(M(reply));
            std::map<std::string, Var>::const_iterator pos;
            pos = reply_m.find("r");
            if (pos == reply_m.end()) {
                // Should decode and throw the right exception.
                prx_->throw_(reply_m.at("e"));
                throw std::runtime_error("should never get here");
            }
            return pos->second;
        }
    private:
        VarProxy* prx_; // not owned
        Result<Var>::Ptr result_;
    };

    /** \brief Part of VarProxy.
     *
     * Specialisation of ProxyCallResult<R> for type void.
     */
    template <>
    class ProxyCallResult<void> : public Result<void>
    {
    public:
        ProxyCallResult(VarProxy* prx, Result<Var>::Ptr result)
            : prx_(prx), result_(result) {}

        virtual void get() const {
            const Var& reply(result_->get()); // {"r": ... } or {"e": ... }
            std::map<std::string, Var> const& reply_m(M(reply));
            std::map<std::string, Var>::const_iterator pos;
            pos = reply_m.find("r");
            if (pos == reply_m.end()) {
                // Should decode and throw the right exception.
                prx_->throw_(reply_m.at("e"));
                throw std::runtime_error("should never get here");
            }
            boost::get<boost::blank>(pos->second);
        }
    private:
        VarProxy* prx_; // not owned
        Result<Var>::Ptr result_;
    };

    /** \brief Part of VarProxy.
     *
     * This is used to turn a Future<Var> into a Future<T>. By adding
     * it as a callback handler to a Future<Var> whose work is to
     * resolve a Future<T> we can set up a Future<T> that resolves
     * when the original Future<Var> does.
     *
     * It resolves the Future<T> with a ProxyCallResult<T> which
     * converts the Var to a T.
     */
    template <typename T>
    class Resolver : public Callback<Var>
    {
    public:
        Resolver(VarProxy* prx, typename Future<T>::Ptr fp)
            : prx_(prx), fp_(fp) {}

        void call(Result<Var>::Ptr rv) {
            fp_->resolve(new ProxyCallResult<T>(prx_, rv));
        }
    private:
        VarProxy* prx_; // not owned.
        typename Future<T>::Ptr fp_;
    };

}

#endif // VAR_PROXY_HGUARD_
