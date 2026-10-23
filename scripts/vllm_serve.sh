#!/usr/bin/env bash
MODEL="$1"
PORT="$2"
shift 2
source /root/vllm_venv/bin/activate
export VLLM_USE_FLASHINFER_SAMPLER=0
exec vllm serve "$MODEL" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --max-model-len 12288 \
    --gpu-memory-utilization 0.86 \
    --max-num-seqs 2 \
    "$@"
