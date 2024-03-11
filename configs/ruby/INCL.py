import math
import m5
from m5.objects import *
from m5.util import convert
from m5.defines import buildEnv
from .Ruby import create_topology
from .Ruby import send_evicts
import re


def define_options(parser):
    # Specify the timing parameters in unit of cpu clock cycle
    l1_latency = 1
    l2_latency = 10
    tdm_slot_width = 3
    resp_bus_slot_width = 3
    parser.add_argument(
        "--l1-latency",
        type=int,
        default=l1_latency,
    )

    parser.add_argument(
        "--l2-latency",
        type=int,
        default=l2_latency
    )

    # TDM slot width is the request bus slot width
    parser.add_argument(
        "--tdm-slot-width",
        type=int,
        default=tdm_slot_width,
        help="TDM slot width used in TDM arbitration in the request bus"
    )

    parser.add_argument(
        "--resp-bus-slot-width",
        type=int,
        default=resp_bus_slot_width,
        help="The number of busy cycles to transmit a response in the response bus"
    )

    parser.add_argument(
        "--num-l2-banks",
        type=int,
        default=8
    )


def create_system(
    options, full_system, system, dma_ports, bootmem, ruby_system, cpus
):
    """
    Configure the ruby system

    :param options: configuration options
    :param full_system: boolean varaible indicating whether use full_system mode
    :param system: system object
    :param dma_ports: list of DMA ports
    :param bootmem: bootmem object
    :param ruby_system: Ruby system object
    :param cpus: list of cpus

    :return: (cpu sequencers, memory controllers, network topology)

    """
    print("Create system is called in INCL.py")

    if buildEnv["PROTOCOL"] != "INCL":
        fatal("This script requires INCL build")

    options.topology = "SnoopingBus"
    options.network = "simple"
    
    if options.num_cpus < 1:
        fatal("This script requires at least one cpu")

    if options.cpu_type != "TimingSimpleCPU":
        fatal("This script requires TimingSimpleCPU cpu model")

    num_llc_banks = options.num_l2_banks
    llc_size_in_bytes = convert.toMemorySize(options.l2_size)
    llc_bank_size = f'{int(llc_size_in_bytes / num_llc_banks)}B'

    # To achieve short switch latency in ruby network, the ruby clock frequency is double of the cpu clock frequency.
    # Thus, all the timing parameters in unit of clock cycle in ruby network must be doubled to account for this change.
    options.l1_latency = options.l1_latency * 2
    options.l2_latency = options.l2_latency * 2
    options.tdm_slot_width = options.tdm_slot_width * 2
    options.resp_bus_slot_width = options.resp_bus_slot_width * 2
    
    cpu_sequencers = []
    l1_cntrl_nodes = []

    block_size_bits = int(math.log(options.cacheline_size, 2))
    l2_bits = int(math.log(num_llc_banks, 2))

    profiler = CustomProfiler()
 
    # Create L1 cache controller
    for i in range(options.num_cpus):

        l1i_cache = RubyCache(
            size=options.l1i_size, 
            assoc=options.l1i_assoc,
            start_index_bit=block_size_bits,
            is_icache = True
        )

        l1d_cache = RubyCache(
            size=options.l1d_size, 
            assoc=options.l1d_assoc, 
            start_index_bit=block_size_bits,
            is_icache = False
        )

        clk_domain = ruby_system.clk_domain

        # Create one unified L1 cache for both instructions and data
        l1_cntrl = L1Cache_Controller(
            version=i,
            L1Icache=l1i_cache,
            L1Dcache=l1d_cache,
            l2_select_num_bits=l2_bits,
            transitions_per_cycle=16,
            clk_domain=clk_domain,
            ruby_system=ruby_system,
            send_evictions=send_evicts(options),
            cache_access_latency=options.l1_latency,
            mandatory_queue_latency=options.l1_latency,
            number_of_TBEs=1,
            profiler=profiler,
        )
        
        # Create sequencer
        cpu_seq = RubySequencer(
            version=i,
            dcache=l1d_cache,
            clk_domain=clk_domain,
            ruby_system=ruby_system,
            max_outstanding_requests=1
        )

        # Set sequencer in L1 controller
        l1_cntrl.sequencer = cpu_seq
        # Set L1 controller in ruby system
        exec("ruby_system.l1_cntrl%d = l1_cntrl" % i)

        cpu_sequencers.append(cpu_seq)
        l1_cntrl_nodes.append(l1_cntrl)

        # Connect L1 controller and the network
        # mandatory queue
        l1_cntrl.mandatoryQueue = MessageBuffer()
        # internal replacement trigger queue
        l1_cntrl.triggerQueue = MessageBuffer(randomization='disabled', allow_zero_latency=True)
        # In ports
        l1_cntrl.busGrantIn = MessageBuffer(ordered=True)
        l1_cntrl.busGrantIn.in_port = ruby_system.network.out_port
        l1_cntrl.requestIn = MessageBuffer(ordered=True)
        l1_cntrl.requestIn.in_port = ruby_system.network.out_port
        l1_cntrl.responseIn = MessageBuffer(ordered=True)
        l1_cntrl.responseIn.in_port = ruby_system.network.out_port
        # Out ports
        l1_cntrl.busRequestOut = MessageBuffer(ordered=True)
        l1_cntrl.busRequestOut.out_port = ruby_system.network.in_port
        l1_cntrl.requestOut = MessageBuffer(ordered=True)
        l1_cntrl.requestOut.out_port = ruby_system.network.in_port
        l1_cntrl.responseOut = MessageBuffer(ordered=False)
        l1_cntrl.responseOut.out_port = ruby_system.network.in_port
    
    # Create L2 caches (LLC)
    l2_cntrl_nodes = []
    l2_index_start = block_size_bits + l2_bits
    r = system.mem_ranges[0]
    for i in range(num_llc_banks):
        cache = RubyCache(
            size=llc_bank_size, 
            assoc=options.l2_assoc, 
            start_index_bit=l2_index_start,
            dataArrayBanks=1,
            tagArrayBanks=1,
            dataAccessLatency=options.l2_latency,
            tagAccessLatency=options.l2_latency,
            resourceStalls=True,
        )
        dir_memory = RubyDirectoryMemory()
        dir_memory.addr_ranges = [
            m5.objects.AddrRange(
                r.start, 
                size=r.size(), 
                intlvHighBit=block_size_bits+l2_bits-1,
                xorHighBit=0,
                intlvBits=l2_bits,
                intlvMatch=i
            )
        ]
        l2_cntrl = L2Cache_Controller(
            version=i,
            directory=dir_memory,
            cacheMemory=cache,
            transitions_per_cycle=16,
            clk_domain=ruby_system.clk_domain,
            ruby_system=ruby_system,
            cache_access_latency=options.l2_latency,
            profiler=profiler,
            maxOutstandingMemRequests=16,
        )

        # Set L2 controller in ruby system
        exec("ruby_system.l2_cntrl%d = l2_cntrl" % i)

        # Connect directory controller and the network
        # in ports
        l2_cntrl.busGrantIn = MessageBuffer(ordered=True)
        l2_cntrl.busGrantIn.in_port = ruby_system.network.out_port
        l2_cntrl.requestIn = MessageBuffer(ordered=True)
        l2_cntrl.requestIn.in_port = ruby_system.network.out_port
        l2_cntrl.responseIn = MessageBuffer(ordered=True)
        l2_cntrl.responseIn.in_port = ruby_system.network.out_port
        # out ports
        l2_cntrl.busRequestOut = MessageBuffer(ordered=True)
        l2_cntrl.busRequestOut.out_port = ruby_system.network.in_port
        l2_cntrl.requestOut = MessageBuffer(ordered=True)
        l2_cntrl.requestOut.out_port = ruby_system.network.in_port
        l2_cntrl.responseOut = MessageBuffer(ordered=False)
        l2_cntrl.responseOut.out_port = ruby_system.network.in_port
        # memory connection
        l2_cntrl.requestToDir = MessageBuffer()
        l2_cntrl.requestToDir.out_port = ruby_system.network.in_port
        l2_cntrl.responseFromDir = MessageBuffer()
        l2_cntrl.responseFromDir.in_port = ruby_system.network.out_port

        l2_cntrl_nodes.append(l2_cntrl)

    # Run each of the ruby memory controllers at a ratio of the frequency of
    # the ruby system
    # clk_divider value is a fix to pass regression.
    ruby_system.memctrl_clk_domain = DerivedClockDomain(
        clk_domain=ruby_system.clk_domain, clk_divider=3
    )

    # create directory
    dir_memory = RubyDirectoryMemory()
    dir_cntrl = Directory_Controller(
        version=0,
        directory=dir_memory,
        l2_select_num_bits=l2_bits,
        transitions_per_cycle=16,
        clk_domain=ruby_system.clk_domain,
        ruby_system=ruby_system,
    )

    # Set directory in ruby system
    ruby_system.dir_cntrl0 = dir_cntrl

    # Connect directory controller and the network
    # in ports
    dir_cntrl.requestIn = MessageBuffer()
    dir_cntrl.requestIn.in_port = ruby_system.network.out_port
    # out ports
    dir_cntrl.responseOut = MessageBuffer()
    dir_cntrl.responseOut.out_port = ruby_system.network.in_port
    # memory connection
    dir_cntrl.requestToMemory = MessageBuffer()
    dir_cntrl.responseFromMemory = MessageBuffer()

    all_cntrls = (
        l1_cntrl_nodes + l2_cntrl_nodes + [dir_cntrl]
    )

    if full_system:
        fatal("This script is missing full system support now")
    
    ruby_system.network.number_of_virtual_networks = 5
    ruby_system.network.endpoint_bandwidth = 1000000
    topology = create_topology(all_cntrls, options)
    return (cpu_sequencers, [dir_cntrl], topology)
