# PECC Internals

For anybody interested in the internal workings of the protocols studied in the PECC paper, this file briefly describes some important aspects of the gem5 implementation that may be useful.

## Memory Model
The two protocols are implemented using gem5 Ruby memory model.  
For details on Ruby memory model, you can check its official gem5 documentation (https://www.gem5.org/documentation/general_docs/ruby/).  
You may also find the tutorial on Ruby useful (https://www.gem5.org/documentation/learning_gem5/part3/MSIintro/).

## Important Files
The following contains the pointers to some important design files:
* `configs/example/se.py`: the top-level configuration script for running simulation in syscall-emulation mode.
* `configs/ruby/<EXCL or INCL>.py`: protocol configuration scripts for EXCL and INCL protocols respectively.
* `src/mem/ruby/protocol/<excl or incl>`: Ruby SLICC implementations of EXCL and INCL protocols respectively.
*  `src/mem/ruby/network/simple/PerfectSwitch.<cc or hh>`: snooping bus and bus arbitration implementation.

## Cache Hierarchy
The two protocols implements the following two-level cache hierarchy:
1. In L1, the cache is a split instruction and data cache that is private to each core. The corresponding Ruby machine type is `L1Cache`.
2. In L2, the cache is a last-level cache (LLC) shared by all cores. The LLC supports multiple banks with set interleaving. Each LLC bank corresponds to Ruby machine type `L2Cache`.
3. The directory (`Directory` Ruby machine type) interfaces between the L2 and the main memory.

## Bus Implementation
Both EXCL and INCL are bus-snooping protocols requiring a bus connecting all the L1 caches and the LLC.
Specifically, the bus is a split-transaction bus consisting of a separate request bus and response bus.
To simulate the bus, the chosen network topology is a network switch connecting all the machines (see `SnoopingBus` topology configuration in `configs/topologies/SnoopingBus.py`).
The separate request bus and response bus are simulated by two distinct virtual channels in the network.
In addition, there is one more virtual channel that is used to communicate the bus request and bus grant signal for request bus arbitration.
The actual implementation of the bus and its arbitration can be found in the design files of the network switch (`src/mem/ruby/network/simple/PerfectSwitch.<cc or hh>`).

### Atomic Request Bus
Both the two protocols require the request bus to be atomic.
An atomic request bus ensures the atomicity of the issurance and observation of a coherence request.
In other words, after a coherence request `r1` is issued, it is not possible to observe another coherence request `r2` before `r1` is observed. 
This is supported by using a dedicated virtual channel in the network to communicate the bus request and bus grant signals.
The inner working is breifly discussed next.
When a L1 controller wants to generate a coherence request, it issues a bus request on this virtual channel.
The switch receives bus requests from L1 controllers by inspecting the incoming messages on this virtual channel. 
According to the arbitration rule, the switch selects a L1 requestor to grant the access to the bus.
This is done by re-routing its bus request signal as a bus grant signal and sending it back to the requestor.
Upon receiving the bus grant signal, the L1 controller inspects the coherence state, generates the correct coherence request, and sends it to the request bus.
The switch generates the bus grant signal periodically, and the period length is sized large enough to ensure the transmitted request in the current slot is processed by all L1 controllers.
Thus, the request bus atomicty is ensured.

### Caveat
The switch model is not suitable to simulate a high-speed bus under the current implementation due to its intrinsic routing delay. 
A simple solution is to scale the clock frequency and timing parameters of Ruby system by a factor as desired and interpret the Ruby latency statistics by dividing that factor. 
For example, the default clock frequency of Ruby system is double of the CPU frequency, and all the timing parameters in Ruby system is double of the specified values.
As a result, the actual latency statistics should be half of the reported latency statistics.

## Atomic Instruction Support
The atomic instruction is supported by locking the accessed cache line inside the L1 cache.
In particular, the atomic instruction is implemented by a pair of lock and unlock memory requests (e.g. load linked and store conditional).
Upon seeing the lock memory request, the L1 controller acquires the write permission to the cache line.
After the acquirement, the L1 controller blocks any remote accesses to that cache line (i.e. lock) until the unlock memory request is observed.
