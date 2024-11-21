# ooo-power-analysis

## Requirements

Compiled gem5.opt binary. Compiled mcpat binary. Python3 and 2.7.

## How to run the code

Put RISCV executable benchmarks in the `benchmarks` directory.

Put the gem5.opt binary at root level, and the mcpat binary in the `mcpat` directory.

Then run the following command:
```
python3 script.py --cpu <cpu> --benchmarks <benchmarks>
```
where `<cpu>` is the CPU model ["minor" or "o3"] and `<benchmarks>` is the benchmark to run.

Additional options for O3 cpu, can be found in the `script.py` file.
