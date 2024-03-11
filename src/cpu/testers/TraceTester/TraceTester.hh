#ifndef __CPU_TESTERS_TRACETESTER_HH__
#define __CPU_TESTERS_TRACETESTER_HH__

#include "mem/port.hh"
#include "params/TraceTester.hh"
#include "sim/clocked_object.hh"

#include <fstream>

namespace gem5
{

class TraceTester : public ClockedObject
{

  public:
    typedef TraceTesterParams Params;
    TraceTester(const Params &p);
    ~TraceTester();

    Port &getPort(const std::string &if_name,
                  PortID idx=InvalidPortID) override;

  protected:
    class CpuPort : public RequestPort
    {
      TraceTester *tester;

      public:

        CpuPort(const std::string &_name, TraceTester *_tester, PortID _id)
            : RequestPort(_name, _tester, _id), tester(_tester)
        { }

      protected:

        bool recvTimingResp(PacketPtr pkt);

        void recvReqRetry()
        { panic("%s does not expect a retry\n", name()); }
    };

    void completeRequest(PacketPtr pkt);
    EventFunctionWrapper wakeupEvent;
    CpuPort port;

  private:

    struct TraceElement
    {
      Cycles timestamp;
      MemCmd cmd; // read or write
      Addr addr;  // physial address of the request
      RequestorID requestorID; // requestor ID
    };
    int id;
    std::string traceFile;
    std::ifstream traceInputStream;
    TraceElement traceElement;

    bool readTrace(TraceElement& element);
    bool sendRequest(TraceElement element);
    void wakeup();
};

} // namespace gem5

#endif // __CPU_TESTERS_TRACETESTER_HH__
