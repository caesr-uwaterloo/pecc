from m5.params import *
from m5.objects import *

from topologies.BaseTopology import SimpleTopology

class SnoopingBus(SimpleTopology):
    description='SnoopingBus'

    def makeTopology(self, options, network, IntLink, ExtLink, Router):

        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency # used by simple and garnet
        router_latency = options.router_latency # only used by garnet

        # Create an individual router for each controller plus one more for
        # the centralized crossbar.  The large numbers of routers are needed
        # because external links do not model outgoing bandwidth in the
        # simple network, but internal links do.
        # For garnet, one router suffices, use CrossbarGarnet.py

        xbar = Router(router_id=0, num_processor=options.num_cpus, tdm_slot_width=options.tdm_slot_width, resp_bus_slot_width=options.resp_bus_slot_width)
        
        network.routers = xbar

        ext_links = [ExtLink(link_id=i, ext_node=n, int_node=xbar, latency=link_latency)
                        for (i, n) in enumerate(self.nodes)]
        network.ext_links = ext_links

        int_links = []
        network.int_links = int_links
