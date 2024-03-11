import system
import multiprocessing
import subprocess
import shlex
import tqdm

from multiprocessing.pool import Pool


def generate_synth_command(protocol, ncore):
    gem5_home = "/gem5"  # Modify here to change the directory path of gem5
    config = f"{protocol}-{ncore}"
    outdir = f"{gem5_home}/synth-out/{config}"

    if protocol == 'INCL':
        command = f"{gem5_home}/build/X86_{protocol}/gem5.opt -d {outdir} {gem5_home}/configs/example/ruby_trace_test.py --ruby --num-cpus {ncore} --l1d_size 16kB --l1i_size 16kB --l2_size 1024kB  --mem-type SimpleMemory --mem-size 8GB"
    else:
        command=f"{gem5_home}/build/X86_{protocol}/gem5.opt -d {outdir} {gem5_home}/configs/example/ruby_random_test.py --ruby --num-cpus {ncore} --l1d_size 256B --l1i_size 256B --l2_size 8192B --mem-type SimpleMemory --maxloads 10000"
    return (command, outdir, config)


def call_proc(args):
    cmd, outdir, config = args
    subprocess.run(f'mkdir -p {outdir}', shell=True)
    with open(f'{outdir}/run_log.txt', 'w') as fp:
        p = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=fp, stderr=subprocess.STDOUT)
        p.communicate(timeout=3600*12*7)
        return (config, p.returncode)


if __name__ == '__main__':
    cmds = []
    for protocol in ['INCL', 'EXCL']:
        for core_count in [2, 3, 4, 5, 6, 7, 8]:
            cmds.append(generate_synth_command(protocol, core_count))

    pool = Pool(8)  # Modify here to configure the number of cores to run the simulation
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
