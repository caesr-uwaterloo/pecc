#include "cpu/testers/TraceTester/TraceTester.hh"
#include "debug/TraceTester.hh"

#include <sstream>

#include "sim/sim_exit.hh"
#include "sim/system.hh"

namespace gem5
{


bool
TraceTester::CpuPort::recvTimingResp(PacketPtr pkt)
{
    tester->completeRequest(pkt);
    return true;
}

TraceTester::TraceTester(const Params &p)
    : ClockedObject(p),
      wakeupEvent([this]{ wakeup(); }, name()),
      port("port", this, p.id),
      id(p.id),
      traceFile(p.traceFile)
{
    traceInputStream.open(p.traceFile, std::ifstream::in);
    if (!traceInputStream.is_open()) {
        fatal("Trace file not found at %s\n", traceFile);
    }

    // kick things into action
    if (readTrace(traceElement)) {
        schedule(wakeupEvent, cyclesToTicks(traceElement.timestamp));
    } else {
        fatal("Trace of cpu %d not found at %s\n", id, traceFile);
    }
}

TraceTester::~TraceTester() {
    if (traceInputStream.is_open()) {
        traceInputStream.close();
    }
}

void
TraceTester::completeRequest(PacketPtr pkt) {
    DPRINTF(TraceTester, "Core %d: Completing %s at address 0x%x, %s\n",
            id,
            pkt->isWrite() ? "write" : "read",
            pkt->getAddr(),
            pkt->isError() ? "error" : "success");
    delete pkt;
    if (readTrace(traceElement)) {
        if (traceElement.timestamp < curCycle()) {
            schedule(wakeupEvent, nextCycle());
        } else {
            schedule(wakeupEvent, cyclesToTicks(traceElement.timestamp));
        }
    } else {
        // Reserve some time for other cores to complete the trace test
        exitSimLoop("Reached trace end", 0, cyclesToTicks(curCycle() + Cycles(1000000)));
    }
}

bool 
TraceTester::readTrace(TraceElement& element) {
    std::string line;
    bool success = false;
    while (getline(traceInputStream, line).good()) {
        uint64_t timestamp;
        int requestorID;
        std::string command;
        Addr addr;
        std::istringstream iss(line);

        if (!(iss >> timestamp >> requestorID >> command >> std::hex >> addr)) {
            panic("Failure in parsing line \"%s\" in trace file %s\n", line, traceFile);
        }

        if (requestorID == id) {
            element.timestamp = Cycles(timestamp);
            element.requestorID = requestorID;
            if (command == "R") {
                element.cmd = MemCmd::ReadReq;
            } else {
                assert(command == "W");
                element.cmd = MemCmd::WriteReq;
            }
            element.addr = addr;
            success = true;
            break;
        }
    }

    return success;
}

void 
TraceTester::wakeup() {
    Cycles current_cycle = curCycle();
    assert(traceElement.timestamp <= current_cycle);
    sendRequest(traceElement);
}

bool
TraceTester::sendRequest(TraceElement element) {
    DPRINTF(TraceTester, "Core %d: Issuing %s at address 0x%x\n",
            id,
            (element.cmd == MemCmd::WriteReq) ? "write" : "read",
            element.addr);
    Request::Flags flags;
    RequestPtr req = std::make_shared<Request>(element.addr, 1, flags, id);
    req->setContext(id);
    uint8_t *pkt_data = new uint8_t[1];
    PacketPtr pkt = new Packet(req, element.cmd);
    pkt->dataDynamic(pkt_data);
    if (!port.sendTimingReq(pkt)) {
       panic("Failed to send request to port %d\n", id);     
    }
    DPRINTF(TraceTester, "Issuing request: requestor %d, command %s, addr 0x%x\n", 
            id, 
            (element.cmd == MemCmd::WriteReq) ? "write" : "read", 
            element.addr);
    return true;
}

Port &
TraceTester::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "port")
        return port;
    else
        return ClockedObject::getPort(if_name, idx);
}


} // namespace gem5
