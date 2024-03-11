// Author: Xinzhe Wang

#ifndef __MEM_RUBY_SLICC_INTERFACE_EXCL_INCLUDES_HH__
#define __MEM_RUBY_SLICC_INTERFACE_EXCL_INCLUDES_HH__

#include <string>

namespace gem5
{

namespace ruby
{

inline int getNumSharer(const NetDest& sharers) {
    return sharers.count();
}

}  // namespace ruby
}  // namespace gem5

#endif // __MEM_RUBY_SLICC_INTERFACE_EXCL_INCLUDES_HH__
