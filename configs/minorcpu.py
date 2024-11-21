import os

import m5
from m5.objects import *
from m5.objects import Cache

import argparse

parser = argparse.ArgumentParser(description="SimpleCPU configuration file",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--cmd', required=True, help="Command to run")
args = parser.parse_args()


class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def connectCPU(self, cpu):
        # need to define this in a base class!
        raise NotImplementedError

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class L1ICache(L1Cache):
    size = '32kB'

    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    size = '32kB'

    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    size = '512kB'
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports


class L3Cache(Cache):
    size = '4MB'
    assoc = 16
    tag_latency = 30
    data_latency = 30
    response_latency = 30
    mshrs = 32
    tgts_per_mshr = 16

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('16GB')]

system.cpu = RiscvMinorCPU()
system.membus = SystemXBar()
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

system.l2bus = L2XBar()
# system.l3bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

system.l2 = L2Cache()
system.l2.connectCPUSideBus(system.l2bus)
system.l2.connectMemSideBus(system.membus)
# system.l2cache.connectMemSideBus(system.l3bus)

# system.l3cache = L3Cache()
# system.l3cache.connectCPUSideBus(system.l3bus)
# system.l3cache.connectMemSideBus(system.membus)

# L1i       L1d
#  |         |
# -------------
#      L2
# -------------
#      |
# -------------
#     L3
# -------------

system.cpu.createInterruptController()
# Connecting memory bus to pio is an x86 thing
# system.cpu.interrupts[0].pio = system.membus.mem_side_ports
# system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
# system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

system.mem_ctrls = MemCtrl()
system.mem_ctrls.dram = DDR3_1600_8x8()
system.mem_ctrls.dram.range = system.mem_ranges[0]
system.mem_ctrls.port = system.membus.mem_side_ports
system.mem_ctrls.dram.read_buffer_size = 512  # Number of entries in read queue
system.mem_ctrls.dram.write_buffer_size = 512  # Number of entries in write queue

binary = os.path.abspath(args.cmd)

# for gem5 V21 and beyond
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print('Exiting @ tick {} because {}'
      .format(m5.curTick(), exit_event.getCause()))
