import m5
from m5.objects import *
from m5.defines import buildEnv
from m5.util import addToPath
import os, argparse, sys

addToPath('../')

from common import Options
from ruby import Ruby

# Get paths we might need.  It's expected this file is in m5/configs/example.
config_path = os.path.dirname(os.path.abspath(__file__))
config_root = os.path.dirname(config_path)

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
Options.addNoISAOptions(parser)

#
# Add the ruby specific and protocol specific options
#
Ruby.define_options(parser)

args = parser.parse_args()

traceFile = f"traces/{args.num_cpus}_core_trace.txt"

#
# Currently ruby does not support atomic or uncacheable accesses
#
cpus = [ TraceTester(id = i, traceFile=traceFile)
         for i in range(args.num_cpus) ]

system = System(cpu = cpus,
                clk_domain = SrcClockDomain(clock = args.sys_clock),
                mem_ranges = [AddrRange(args.mem_size)])

Ruby.create_system(args, False, system, dma_ports = [])

# Create a top-level voltage domain and clock domain
system.voltage_domain = VoltageDomain(voltage = args.sys_voltage)
system.clk_domain = SrcClockDomain(clock = "2GHz",
                                   voltage_domain = system.voltage_domain)
# Create a seperate clock domain for Ruby
system.ruby.clk_domain = SrcClockDomain(clock = "4GHz",
                                        voltage_domain = system.voltage_domain)

system.ruby.randomization = False

assert(len(cpus) == len(system.ruby._cpu_ports))

for (i, cpu) in enumerate(cpus):
    #
    # Tie the cpu memtester ports to the correct system ports
    #
    cpu.port = system.ruby._cpu_ports[i].in_ports

    # Set deadlock threshold
    system.ruby._cpu_ports[i].deadlock_threshold = 5000000

# -----------------------
# run simulation
# -----------------------

root = Root( full_system = False, system = system )
root.system.mem_mode = 'timing'

# Not much point in this being higher than the L1 latency
m5.ticks.setGlobalFrequency('0.25ns')

# instantiate configuration
m5.instantiate()

# simulate until program terminates
exit_event = m5.simulate(args.abs_max_tick)

print('Exiting @ tick', m5.curTick(), 'because', exit_event.getCause())
