#ifndef FUTURE_HGUARD_
#define FUTURE_HGUARD_

#include <string>
#include <stdexcept>
#include <boost/shared_ptr.hpp>

namespace serf {

    template <typename T>
    struct add_constref {
        typedef T const& type;
    };

    template <>
    struct add_constref<void> {
        typedef void type;
    };

    template <typename T>
    struct non_void {
        typedef T type;
    };

    template <>
    struct non_void<void> {
        typedef int type;
    };

     /** \brief What a Future gives to its callback function.
      */
    template <typename R>
    class Result {
    public:
        typedef typename add_constref<R>::type ref_type;
        typedef typename boost::shared_ptr<Result> Ptr;

        virtual ~Result() {}

        virtual ref_type get() const = 0;
    };

    /** \brief Holds a return value for a Future.
     */
    template <typename R>
    class ValueResult : public Result<R> {
    public:
        typedef typename add_constref<R>::type ref_type;

        ValueResult(R const& result)
            : result_(result) {}

        virtual ref_type get() const {
            return result_;
        }

    public:
        R result_;
    };

    class VoidResult : public Result<void> {
    public:
        virtual void get() const {
        }
    };

    /** \brief Holds a runtime_error for a Future.
     */
    template <typename R>
    class ErrorResult : public Result<R> {
    public:
        typedef typename add_constref<R>::type ref_type;

        ErrorResult(std::string const& what) : what_(what) {}
        
        virtual ref_type get() const {
            throw std::runtime_error(what_);
        }
    private:
        std::string what_;
    };
    
    /** \brief Something we can pass a Result to when a Future is resolved.
     */
    template <typename R>
    class Callback {
    public:
        virtual ~Callback() {}

        virtual void call(typename Result<R>::Ptr result) = 0;
    };

    /** \brief A bound member function Callback.
     */
    template <typename T, typename R>
    class MemFnCallback : public Callback<R> {
    public:
        typedef void (T::*memfn_ptr)(typename Result<R>::Ptr);

        MemFnCallback(T* inst, memfn_ptr memfn) : inst_(inst), memfn_(memfn) {}

        virtual void call(typename Result<R>::Ptr result) {
            (inst_->*memfn_)(result);
        }

    private:
        T* inst_; // not owned.
        memfn_ptr memfn_;
    };

    /** \brief Placeholder for a result not yet available.
     */
    template <typename R>
    class Future
    {
    public:

        typedef boost::shared_ptr<Future> Ptr;
        typedef typename add_constref<R>::type ref_type;

        Future() : callback_(NULL) {
        }

        ~Future() {
            delete callback_;
        }

        void then(Callback<R>* callback) {
            if (callback_) throw std::runtime_error("callback already set");
            callback_ = callback;
            if (result_) {
                callback_->call(result_);
            }
        }

        template <typename T>
        void then(T* inst, void (T::*memfn)(typename Result<R>::Ptr)) {
            then(new MemFnCallback<T, R>(inst, memfn));
        }

        typedef typename non_void<R>::type NVR;
        
        void resolve(NVR const& value) {
            resolve(new ValueResult<NVR>(value));
        }

        void resolve() {
            resolve(new VoidResult());
        }

        void resolve(Result<R>* result) { // takes ownership.
            if (result_) throw std::runtime_error("result already set");
            result_.reset(result);
            if (callback_) {
                callback_->call(result_);
            }
        }

		ref_type get() {
			if (!result_) throw std::runtime_error("future not yet resolved");
			return result_->get();
		}

    private:
        typename Result<R>::Ptr result_;
        Callback<R>* callback_; // owned
    };
}

#endif // FUTURE_HGUARD_
