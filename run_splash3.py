import system
import multiprocessing
import subprocess
import shlex
import tqdm

from multiprocessing.pool import Pool


def generate_splash3_command(program, protocol, ncore, llc_size, l1d_size="16kB", l1i_size="16kB", mem_size="1GB"):
    gem5_home = "/gem5"  # Modify here to change the directory path of gem5
    splash3_dir = f"{gem5_home}/splash-3-static-link/codes"
    config = f"{program}_{protocol}_{ncore}_{llc_size}"
    binary = ""
    stdin = ""
    options = ""
    wkdir = ""
    outdir = f"{gem5_home}/splash-3-out/{config}"

    if program == 'barnes':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=""
        stdin=f"{splash3_dir}/apps/{program}/inputs/n65536-p{ncore}"
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'fmm':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=""
        stdin=f"{splash3_dir}/apps/{program}/inputs/input.{ncore}.65536"
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'ocean':
        binary=f"{splash3_dir}/apps/{program}/contiguous_partitions/{program.upper()}"
        options=f"-p{ncore} -n514"
        stdin=""
        wkdir=f"{splash3_dir}/apps/{program}/contiguous_partitions"
    elif program == 'radiosity':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=f"-p {ncore} -ae 5000 -bf 0.015 -en 0.05 -room -batch"
        stdin=""
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'raytrace':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=f"-p{ncore} -m64 {splash3_dir}/apps/{program}/inputs/balls4.env"
        stdin=""
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'volrend':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=f"{ncore} {splash3_dir}/apps/{program}/inputs/head 8"
        stdin=""
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'water-nsquared':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=""
        stdin=f"{splash3_dir}/apps/{program}/inputs/n3375-p{ncore}"
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'water-spatial':
        binary=f"{splash3_dir}/apps/{program}/{program.upper()}"
        options=""
        stdin=f"{splash3_dir}/apps/{program}/inputs/n8000-p{ncore}"
        wkdir=f"{splash3_dir}/apps/{program}"
    elif program == 'cholesky':
        binary=f"{splash3_dir}/kernels/{program}/{program.upper()}"
        options=f"-p{ncore}"
        stdin=f"{splash3_dir}/kernels/{program}/inputs/tk16.O"
        wkdir=f"{splash3_dir}/kernels/{program}"
    elif program == 'fft':
        binary=f"{splash3_dir}/kernels/{program}/{program.upper()}"
        options=f"-p{ncore} -m22 -l6 -n16384"
        stdin=""
        wkdir=f"{splash3_dir}/kernels/{program}"
    elif program == 'lu':
        binary=f"{splash3_dir}/kernels/{program}/contiguous_blocks/{program.upper()}"
        options=f"-p{ncore} -n1024"
        stdin=""
        wkdir=f"{splash3_dir}/kernels/{program}/contiguous_blocks"
    elif program == 'radix':
        binary=f"{splash3_dir}/kernels/{program}/{program.upper()}"
        options=f"-p{ncore} -n4194304"
        stdin=""
        wkdir=f"{splash3_dir}/kernels/{program}"
    else:
        print("Unknown program")
        system.exit(-1)
    
    command = f"{gem5_home}/build/X86_{protocol}/gem5.opt -d {outdir} {gem5_home}/configs/example/se.py --ruby --num-cpus {ncore} --cpu-type TimingSimpleCPU --l1d_size {l1d_size} --l1i_size {l1i_size} --l2_size {llc_size} --mem-type SimpleMemory --mem-size {mem_size} -c {binary} --options=\"{options}\""
    if stdin:
        command += f" < {stdin}"
    
    return (command, wkdir, outdir, config)



def call_proc(args):
    cmd, wkdir, outdir, config = args
    subprocess.run(f'mkdir -p {outdir}', shell=True)
    with open(f'{outdir}/run_log.txt', 'w') as fp:
        p = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=fp, stderr=subprocess.STDOUT, cwd=wkdir)
        p.communicate(timeout=3600*12*7)
        return (config, p.returncode)


if __name__ == '__main__':
    # Generate the commands to run Splash-3 benchmarks
    programs = ['barnes','fmm','ocean','radiosity','raytrace','water-nsquared','water-spatial','cholesky','fft','lu','radix']

    cmds = []
    for program in programs:
        if program == 'raytrace':
            mem_size = '8GB'
        else:
            mem_size = '1GB'

        for protocol in ['INCL', 'EXCL']:
            for core_count in [2, 4]:
                for llc_size in ['1024kB']:
                    cmds.append(generate_splash3_command(program, protocol, core_count, llc_size, mem_size=mem_size))

            for core_count in [8]:
                for llc_size in ['256kB', '512kB', '1024kB']:
                    cmds.append(generate_splash3_command(program, protocol, core_count, llc_size, mem_size=mem_size))

    pool = Pool(31)  # Modify here to configure the number of cores to run the simulation
    results = list(tqdm.tqdm(pool.imap_unordered(call_proc, cmds), total=len(cmds)))
    pool.close()
    pool.join()
    
    failure = 0
    failed_configs = []
    for config, retcode in results:
        if retcode != 0:
            failed_configs.append((config, retcode))
    print(f"Splash3 run completes: {len(cmds) - len(failed_configs)} out of {len(cmds)} passes")
    if failed_configs:
        print("Failed experiments:")
        for config, retcode in failed_configs:
            print(f"{config}: retcode {retcode}")
