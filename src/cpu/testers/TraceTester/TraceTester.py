from m5.params import *
from m5.proxy import *

from m5.objects.ClockedObject import ClockedObject

class TraceTester(ClockedObject):
    type = 'TraceTester'
    cxx_header = "cpu/testers/TraceTester/TraceTester.hh"
    cxx_class = 'gem5::TraceTester'

    id = Param.Int("Cpu ID")
    #timeout = Param.Cycles(10000, "Timeout cycles for request response")
    traceFile = Param.String("", "Memory trace file")
    #system = Param.System(Parent.any, "System this tester is part of")

    port = RequestPort("Port to the memory system")
