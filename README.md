# poi-invariants-pro

Production-ready skeleton for verifiable AI inference (AI × ZK), shipping:
- Deterministic IR → Circom codegen with strict range gates (`x ∈ [-B,B]` enforced via `< 2B+1`)
- Cross-implementation equivalence (Circom vs Python reference evaluator)
- Proof-system backend (Groth16 via snarkjs) with SRS lifecycle & manifest
- Auditable receipts (IR/R1CS/SRS-manifest/SRS/VK/proof/tool versions)
- Benchmarks (S/M tiers) with constraints/time/RSS/proof metrics
- nsjail sandbox (no network, read-only, seccomp)
- Reproducible builds & supply-chain pinning (hash gate), SBOM target

## Quickstart

```bash
# Prereqs: Node.js, snarkjs, circom, nsjail, jq, curl
npm i -g snarkjs

python -m venv .venv && . .venv/bin/activate
pip install -e .

# Fetch SRS (fail-closed on hash mismatch)
bash scripts/fetch_srs.sh artifacts/pot12_final.ptau

# S-tier benchmark (fast: 32×32 matmul + softmax-like poly)
poi bench --ir benchmarks/ir/mm32_soft64.json \
          --values benchmarks/values/mm32_soft64.values.json \
          --workdir .work/bench/s \
          --out benchmarks/results/s.json

# Prove & verify (Groth16)
poi prove  --ir benchmarks/ir/mm32_soft64.json \
           --values benchmarks/values/mm32_soft64.values.json \
           --workdir .work/prove > .work/prove/out.json
jq . .work/prove/out.json
poi verify --vkey "$(jq -r .vkey .work/prove/out.json)" \
           --public "$(jq -r .public .work/prove/out.json)" \
           --proof  "$(jq -r .proof  .work/prove/out.json)"

# Make receipt (bind all hashes)
poi receipt make --ir benchmarks/ir/mm32_soft64.json \
                 --workdir .work/prove \
                 --r1cs .work/prove/build/main.r1cs \
                 --srs artifacts/pot12_final.ptau \
                 --vkey .work/prove/build/vkey.json \
                 --proof .work/prove/build/proof.json \
                 --out receipts/last.json

# Cross-impl equivalence (Circom public outputs vs Python reference)
poi equiv --ir benchmarks/ir/mm32_soft64.json \
          --values benchmarks/values/mm32_soft64.values.json \
          --workdir .work/equiv
