import argparse
import subprocess
import os
import shutil

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run benchmark with specified configuration and process results.")
    parser.add_argument('--cpu', required=True, choices=['minor', 'o3'], help='Type of CPU: minor or o3')
    parser.add_argument('--width', type=int, default=8, help='Issue width')
    parser.add_argument('--lqsq', type=int, default=32, help='Load/Store queue size')
    parser.add_argument('--rob', type=int, default=192, help='Reorder buffer size')
    parser.add_argument('--iq', type=int, default=64, help='Instruction queue size')
    parser.add_argument('--benchmark', required=True, help='Benchmark binary to run')
    return vars(parser.parse_args())

def construct_filename(config):
    filename = f"{config['cpu']}"
    if config['cpu'] == 'o3':
        for key in ['width', 'lqsq', 'rob', 'iq']:
            if config[key] is not None:
                filename += f"-{key}{config[key]}"
    filename += f"-{config['benchmark'].split('/')[-1]}"
    return filename

def run_gem5(config, filename):
    config_file = f"configs/{config['cpu']}cpu.py"
    stats_file = f"stats/{filename}_stats.txt"
    json_file = f"config/{filename}_config.json"
    result_file = f"benchmark_results/{filename}_result"
    cmd = f"./gem5.opt -r --stdout-file={result_file} --stats-file={stats_file} --json-config={json_file} {config_file} --cmd=./benchmarks/{config['benchmark']}"
    if config['cpu'] == 'o3':
        for key in ['width', 'lqsq', 'rob', 'iq']:
            if config[key] is not None:
                cmd += f" --{key} {config[key]}"

    subprocess.run(cmd, shell=True, check=True)

def parse_stats(config, filename):
    stats_file = f"m5out/stats/{filename}_stats.txt"
    config_file = f"m5out/config/{filename}_config.json"
    template_file = f"templates/template-{config['cpu']}.xml"
    output_xml = f"m5out/parsed/{filename}.xml"
    cmd = f"python2.7 parser.py {stats_file} {config_file} {template_file} -o {output_xml}"
    subprocess.run(cmd, shell=True, check=True, executable='/bin/bash')

def run_mcpat(filename):
    input_xml = f"m5out/parsed/{filename}.xml"
    output_txt = f"mcpat/output/{filename}.txt"
    cmd = f"./mcpat/mcpat -infile {input_xml} > {output_txt} -print_level 5 -opt_for_clk 1"
    subprocess.run(cmd, shell=True, check=True)

def main():
    config = parse_arguments()
    filename = construct_filename(config)
    print(config)
    print(filename)

    run_gem5(config, filename)
    parse_stats(config, filename)
    run_mcpat(filename)

if __name__ == "__main__":
    main()
