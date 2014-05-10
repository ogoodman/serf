#include <serf/rpc/var_callable.h>

#include <sstream>
#include <serf/rpc/serf_exception.h>

namespace serf {

    /** \brief Part of VarCallable.
     *
     * This helper directly resolves a Future<Var> with the result of
     * a call to VarCallable.varCall_a_(method, args).
     * Because it does not know how to encode all possible exceptions
     * which a given VarCallable may throw, it causes the call to
     * be executed inside a call to try_ which should
     * know how to encode all exceptions specific to the instance.
     */
    class VarCallableCaller : public Runnable {
    public:
        // FIXME: the body of this can go into var_callable.cpp.
        VarCallableCaller(VarCallable* callable, std::string const& method, std::vector<Var> const& args)
            : callable_(callable), method_(method), args_(args) {}

		/** \brief Makes a call on a VarCallable returning an encoded
		 *  result or exception.
		 *
		 * The Result<Var> which the returned Future<Var> is resolved
		 * with should never throw. Any exceptions raised when the
		 * VarCallable is called should be caught and encoded.
		 */
        FVarP& call() {
            Var exc;
            if (!callable_->try_(*this, exc)) {
                std::map<std::string, Var> enc;
                enc["e"] = exc;
                f_result_.reset(new Future<Var>());
                f_result_->resolve(Var(enc));
            }
            // else f_result_ will have been resolved in this->get().
            return f_result_;
        }

		/** \brief Makes a call on a VarCallable.
		 */
        virtual void run() {
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

    VarCallable::~VarCallable() {}

    bool VarCallable::try_(Runnable& runnable, Var& exc) {
        try {
            runnable.run();
            return true;
		} catch (SerfException& e) {
			exc = e.encode();
		} catch (boost::bad_get& e) {
			std::vector<Var> exc_v(2);
			exc_v[0] = std::string("TypeError");
			exc_v[1] = std::string(e.what());
			exc = exc_v;
        } catch (std::exception& e) {
			std::vector<Var> exc_v(2);
            exc_v[0] = std::string("Exception");
            exc_v[1] = std::string(e.what());
			exc = exc_v;
        } catch (...) {
			std::vector<Var> exc_v(2);
            exc_v[0] = std::string("Exception");
            exc_v[1] = std::string("C++ unknown type");
			exc = exc_v;
		}
		return false;
    }

    /** \brief Dispatches calls to methods of the implementation.
     *
     * The result is returned as a Future<Var> resolving to
     * {"r": result}. 
     * Any exception thrown is converted by try_ to a Var and
     * returned as {"e": exception}.
     */
	FVarP VarCallable::call_(std::string const& method, std::vector<Var> const& args) {
        return VarCallableCaller(this, method, V(args)).call();
	}

    /** \brief Converts a Var to a Future<Var> of {"r": result}.
     */
    FVarP VarCallable::encodeResult_(Var const& result) {
		std::map<std::string, Var> m_var;
		m_var["r"] = result;
		FVarP f_res(new Future<Var>());
		f_res->resolve(Var(m_var));
        return f_res;
    }
}
