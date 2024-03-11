from m5.params import *
from m5.SimObject import SimObject

class CustomProfiler(SimObject):
    type = 'CustomProfiler'
    cxx_class = 'gem5::ruby::CustomProfiler'
    cxx_header = 'mem/ruby/profiler/CustomProfiler.hh'
    
