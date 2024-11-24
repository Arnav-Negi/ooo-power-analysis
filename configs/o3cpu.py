import os

import m5
from m5.objects import *
from m5.objects import Cache

import argparse

parser = argparse.ArgumentParser(description="O3CPU configuration file",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--cmd', required=True, help="Command to run")
parser.add_argument('--width', type=int, default=8, help='Issue width')
parser.add_argument('--lqsq', type=int, default=32, help='Load/Store queue size')
parser.add_argument('--rob', type=int, default=192, help='Reorder buffer size')
parser.add_argument('--iq', type=int, default=64, help='Instruction queue size')
args = parser.parse_args()


class L1Cache(Cache):
    assoc = 16

    tag_latency = 1
    data_latency = 1
    response_latency = 1

    mshrs = 128
    tgts_per_mshr = 16
    write_buffers = 56
    demand_mshr_reserve = 96

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
    assoc = 16

    tag_latency = 14
    data_latency = 14
    response_latency = 1

    mshrs = 256
    tgts_per_mshr = 16
    write_buffers = 256

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

system.cpu = RiscvO3CPU()
# O3 cpu is a 5 stage pipeline
system.cpu.issueWidth = 8  # widths of the other pipeline stages (decode, rename etc) are also 8
system.cpu.numROBEntries = 192
system.membus = SystemXBar()
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

system.l2 = L2Cache()
system.l2.connectCPUSideBus(system.l2bus)
system.l2.connectMemSideBus(system.membus)

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
