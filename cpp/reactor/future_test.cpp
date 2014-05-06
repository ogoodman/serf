#include <serf/reactor/future.h>
#include <cxxtest/TestSuite.h>

#include <serf/serializer/var.h>

using namespace serf;

class FutureTest : public CxxTest::TestSuite
{
public:
    void helper(Result<int>::Ptr r) {
        try {
            n = r->get();
        } catch (std::exception& e) {
            ++tc;
        }
    }

    void vhelper(Result<void>::Ptr r) {
        try {
            r->get();
            n += 2;
        } catch (std::exception& e) {
            ++tc;
        }
    }

    void testFuture() {
        n = 0;
        Future<int> f;
        
        f.then(this, &FutureTest::helper);

        TS_ASSERT_EQUALS(n, 0);

        f.resolve(1);

        TS_ASSERT_EQUALS(n, 1);

        Future <int> g;
        g.resolve(2);

        g.then(this, &FutureTest::helper);

        TS_ASSERT_EQUALS(n, 2);
    }

    void testFutureException() {
        n = 0;
        tc = 0;

        Future<int> f;
        
        f.then(this, &FutureTest::helper);

        TS_ASSERT_EQUALS(n, 0);

        f.resolve(new ErrorResult<int>("bang"));

        TS_ASSERT_EQUALS(n, 0);
        TS_ASSERT_EQUALS(tc, 1);

        Future <int> g;
        g.resolve(new ErrorResult<int>("kaboom"));

        g.then(this, &FutureTest::helper);

        TS_ASSERT_EQUALS(n, 0);
        TS_ASSERT_EQUALS(tc, 2);
    }

    void testFutureVoid() {
        n = 0;

        Future<void> f;
        f.then(this, &FutureTest::vhelper);

        TS_ASSERT_EQUALS(n, 0);

        f.resolve();

        TS_ASSERT_EQUALS(n, 2);
    }
private:
    int n;
    int tc;
};
