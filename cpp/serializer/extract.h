#ifndef EXTRACT_HGUARD_
#define EXTRACT_HGUARD_

#include <serf/serializer/var.h>

namespace serf {

    /** \brief Similar to boost::get, this can also recursively
     *  extract into homogeneous containers.
     *
     * By itself, boost::get<T> with T = vector<int> cannot get
     * a vector<int> from a Var whose value is a vector<Var> with
     * each Var being an int.
     *
     * Similarly we cannot assign a vector<int> to a Var.
     */
    template <typename T>
    struct Extract {
        static void extract(T& target, Var const& value) {
            target = boost::get<const T&>(value);
        }
        static void setVar(Var& var, T const& value) {
            var = value;
        }
    };

    /** \brief See Extract<T>. Specialization for Var.
     *
     * This is needed because boost::get<Var> throws bad_get.
     */
    template <>
    struct Extract<Var> {
        static void extract(Var& target, Var const& value) {
            target = value;
        }
        static void setVar(Var& var, Var const& value) {
            var = value;
        }
    };

    /** \brief See Extract<T>. Specialization for vectors.
     */
    template <typename E>
    struct Extract< std::vector<E> > {
        typedef typename std::vector<E> type;
        static void extract(type& e_vec, Var const& value) {
            size_t i, n = V(value).size(); // V gets a vector<Var>&.
            for (i = 0; i < n; ++i) {
                E elem;
                Extract<E>::extract(elem, V(value)[i]);
                e_vec.push_back(elem);
            }
        }
        static void setVar(Var& var, type const& value) {
            size_t i, n = value.size();
            std::vector<Var> v_vec(n);
            for (i = 0; i < n; ++i) {
                Extract<E>::setVar(v_vec[i], value[i]);
            }
            var = v_vec;
        }
    };

    /** \brief See Extract<T>. Specialization for maps.
     */
    template <typename E>
    struct Extract< std::map<std::string, E> > {
        typedef typename std::map<std::string, E> type;
        static void extract(type& e_dict, Var const& value) {
             // M gets a map<string, Var>&
            std::map<std::string, Var>::const_iterator it, e = M(value).end();
            for (it = M(value).begin(); it != e; ++it) {
                E elem;
                Extract<E>::extract(elem, it->second);
                e_dict[it->first] = elem;
            }
        }
        static void setVar(Var& var, type const& value) {
            typename type::const_iterator it, e = value.end();
            std::map<std::string, Var> v_dict;
            for (it = value.begin(); it != e; ++it) {
                Extract<E>::setVar(v_dict[it->first], it->second);
            }
            var = v_dict;
        }
    };

    /** \brief Similar to boost::get, this can also recursively
     *  extract into homogeneous containers.
     *
     * This is a convenience wrapper for a call to Extract<T>::extract.
     */
    template <typename T>
    void extract(T& to, Var const& value) {
        Extract<T>::extract(to, value);
    }

    /** \brief The opposite of extract, this turns a suitable homogeneous
     *  container type value into a Var.
     *
     * This is a convenience wrapper for a call to Extract<T>::setVar.
     */
    template <typename T>
    void setVar(Var& var, T const& value) {
        Extract<T>::setVar(var, value);
    }

}

#endif // EXTRACT_HGUARD_
