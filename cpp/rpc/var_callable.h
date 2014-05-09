#ifndef VAR_CALLABLE_HGUARD_
#define VAR_CALLABLE_HGUARD_

#include <stdexcept>
#include <serf/serializer/var.h>
#include <serf/serializer/extract.h>
#include <serf/reactor/future.h>

namespace serf {

    typedef boost::shared_ptr<Future<Var> > FVarP;

    class VarCallable;

    /** \brief Part of VarCallable.
     *
     * This enables us to convert a Future<R>, returned by calling
     * a method of a VarCallable's eventual implementation, into
     * a Future<Var> which encodes the result or exception. So the
     * Future<Var> itself should never throw: in the event that the
     * Future<R> throws, the exception is encoded as a Var result for
     * the Future<Var>.
     *
     * It provides a callback for the Future<R> which attempts to
     * get the R result and encode it as {"r": result}. If this fails
     * it instead encodes the result as {"e": exc}.
     *
     * Because it cannot know how to encode every exception which can
     * possibly occur it uses a helper function tryGet_ of the original
     * VarCallable to indirectly call Result<R>.get(). Its implementation
     * should catch and encode any exception the VarCallable might throw.
     * We pass ourself to tryGet_ as a Result<void> which tryGet_
     * must call get() on. That get() is where we can attempt to extract
     * and convert the R result, knowing that tryGet_ will catch any
     * exception that is thrown.
     */
    template <typename R>
    class VarCallResolver : public Callback<R>, public Result<void> {
    public:
        typedef typename Future<R>::Ptr f_type;

        VarCallResolver(VarCallable* callable, f_type f, FVarP f_result)
            : callable_(callable), f_(f), f_result_(f_result) {}

        virtual void call(typename Result<R>::Ptr result);

        virtual void get() const {
            std::map<std::string, Var> enc;
            setVar(enc["r"], r_result_->get());
            f_result_->resolve(Var(enc));
        }
    private:
        VarCallable* callable_;
        f_type f_;
        mutable FVarP f_result_;
        typename Result<R>::Ptr r_result_;
    };
    
    /** \brief Interface which remotely callable instances must implement.
     */
    class VarCallable
    {
    public:
        virtual ~VarCallable();

        /** \brief Calls result.get() and encodes any exception which occurs
         *  in exc.
         *
         * Returns true if get() returns normally, false if get() throws.
         */
        virtual bool tryGet_(Result<void>& result, Var& exc);

        /** \brief Converts a Future<R> to a Future<Var> which resolves to
         *  the encoded result.
         *
         * The result of the returned Future<Var> will be {"r": result}
         * if f resolves to an R and R can be encoded to a Var, while
         * it will be {"e": exc} if the resolution of f throws or if
         * R cannot be converted to a Var for any reason.
         */
        template <typename R>
        FVarP toFuture(typename Future<R>::Ptr f) {
            FVarP result(new Future<Var>);
            f->then(new VarCallResolver<R>(this, f, result));
            return result;
        }

        virtual Var varCall_(std::string const& method, std::vector<Var> const& args) = 0;
        virtual FVarP varCall_a_(std::string const& method, std::vector<Var> const& args) = 0;
    };

    template <typename R>
    void VarCallResolver<R>::call(typename Result<R>::Ptr result) {
        Var exc;
        r_result_ = result;
        if (!callable_->tryGet_(*this, exc)) {
            std::map<std::string, Var> enc;
            enc["e"] = exc;
            f_result_->resolve(Var(enc));
        }
        // else f_result_ will have been resolved in this->get().
    }


    /** \brief Part of VarCallable.
     *
     * This helper directly resolves a Future<Var> with the result of
     * a synchronous call to VarCallable.varCall_(method, args).
     * Because it does not know how to encode all possible exceptions
     * which a given VarCallable may throw, it causes the call to
     * varCall_ to be executed inside a call to tryGet_ which should
     * know how to encode all exceptions specific to the instance.
     */
    class SyncVarCallResolver : public Result<void> {
    public:
        // FIXME: the body of this can go into var_callable.cpp.
        SyncVarCallResolver(VarCallable* callable, std::string const& method, std::vector<Var> const& args)
            : callable_(callable), method_(method), args_(args) {}

        FVarP& resolve() {
            Var exc;
            if (!callable_->tryGet_(*this, exc)) {
                std::map<std::string, Var> enc;
                enc["e"] = exc;
                f_result_.reset(new Future<Var>());
                f_result_->resolve(Var(enc));
            }
            // else f_result_ will have been resolved in this->get().
            return f_result_;
        }

        virtual void get() const {
            // If this returns we will eventually get a packaged
            // result or a packged exception, but not an exception.
            f_result_ = callable_->varCall_a_(method_, args_);
        }

    private:
        VarCallable* callable_;
        std::string method_;
        std::vector<Var> args_;
        mutable FVarP f_result_;
    };

    class VarCallException : public std::exception
    {
    public:
        VarCallException();
        VarCallException(std::string const& what);
        ~VarCallException() throw() {}

        const char* what() const throw() {
            return msg_.c_str();
        }
    protected:
        std::string msg_;
    };

    class NoSuchMethod : public VarCallException
    {
    public:
        NoSuchMethod(std::string const& method);
    };

    class NotEnoughArgs : public VarCallException
    {
    public:
        NotEnoughArgs(std::string const& method, int provided, int required);
    };
}

#endif // VAR_CALLABLE_HGUARD_
