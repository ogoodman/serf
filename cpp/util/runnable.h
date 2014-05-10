#ifndef RUNNABLE_HGUARD_
#define RUNNABLE_HGUARD_

namespace serf {

	/** \brief A simple task. See also Task.
	 */
    class Runnable
    {
	public:
		~Runnable();

		/** \brief Run the task.
		 */
		virtual void run() = 0;
    };
}

#endif // RUNNABLE_HGUARD_
