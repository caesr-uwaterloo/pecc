#!/bin/bash
protocol=$1

if [ "$protocol" = "INCL" ] || [ "$protocol" = "EXCL" ]; then 
    scons build/X86_$protocol/gem5.opt --default=X86 PROTOCOL=$protocol --ignore-style -j31 2>&1 | tee build_log.txt
else
    echo "Error: Protocol name should be INCL or EXCL"
fi