# gem5 for PECC
This repository is a fork of [the official gem5 repository](https://github.com/gem5/gem5) (Version 22.0.0.2) that implements the two coherence protocols studied in the PECC paper:
1. PECC protocol (gem5 protocol name: `EXCL`)
2. Conventional MOESI protocol for inclusive cache (gem5 protocol name: `INCL`)

Note that this repo does not contain ZCLLC implementation because it is a separate work.

## Dependencies
The required dependencies are the same as for official gem5 (Version 22.0.0.2). Please refer to [the official gem5 build instruction](https://www.gem5.org/documentation/general_docs/building#dependencies).
Additionally, the experiment launching scripts (`run_synth.py` and `run_splash3.py`) require python `tqdm` library for progress monitoring.

We also provide the Dockerfile with all the required dependencies.
To use docker:
1. Build the image: run `docker build -t gem5-pecc:latest .` inside the repo directory.
2. Launch the container: `docker run -u $UID:$GID --volume <pecc repo directory>:/gem5 --rm -it gem5-pecc:latest`

## Usage
Assuming using docker container, in the directory `/gem5`:
1. Build the two protocols: `./build.sh EXCL` and `./build.sh INCL`
2. Run synthetic benchmark: `python3 run_synth.py`. The experiment results are stored under `synth-out`.
3. Run Splash3 benchmark: `python3 run_splash3.py`. The experiment results are stored under `splash-3-out`.

## Internal Workings
For information on the internal workings of the two protocols, `PECC-INTERNAL.md` breifly documents some important aspects of the gem5 implementations of the two protocols.