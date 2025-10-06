# poi_invariants_pro/util.py
from __future__ import annotations
import os, sys, json, time, shutil, subprocess
from pathlib import Path
import sha3  # pysha3 hard dependency

P_BN254 = 21888242871839275222246405745257275088548364400416034343698204186575808495617

class ApiError(Exception):
    def __init__(self, code: str, msg: str, retryable: bool=False, evidence: dict|None=None):
        super().__init__(msg)
        self.code, self.msg, self.retryable = code, msg, retryable
        self.evidence = evidence or {}
    def to_dict(self): return {"error": self.msg, "code": self.code, "retryable": self.retryable, "evidence": self.evidence}

def raise_err(code, msg, **kw): raise ApiError(code, msg, **kw)

def keccak_hex(b: bytes) -> str:
    return sha3.keccak_256(b).hexdigest()

def sha256_hex(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def version_info():
    from . import __version__
    def ver(cmd):
        try:
            out = subprocess.check_output([cmd,"--version"], text=True)
            return out.strip().splitlines()[0]
        except Exception: return ""
    return {
        "poi": __version__,
        "circom": ver("circom"),
        "snarkjs": ver("snarkjs"),
        "nsjail": ver("nsjail")
    }

def run_in_sandbox(argv: list[str], timeout_s: int = 600) -> subprocess.CompletedProcess:
    ns = shutil.which("nsjail")
    if not ns:
        raise_err("E_SANDBOX", "nsjail not installed; required")
    seccomp = os.getenv("POI_SECCOMP", "config/seccomp.policy")
    cmd = [
        ns, "--quiet",
        "--clone_newnet", "--iface_no_lo",
        "--chroot","/", "--cwd","/",
        "--disable_proc",
        "--seccomp_policy", seccomp,
        "--bindmount_ro","/usr",
        "--bindmount_ro","/bin",
        "--bindmount_ro","/lib",
        "--bindmount_ro","/lib64",
        "--rlimit_as", os.getenv("POI_RLIMIT_AS_MB","4096"),
        "--rlimit_cpu", os.getenv("POI_RLIMIT_CPU_S","600"),
        "--rlimit_fsize", os.getenv("POI_RLIMIT_FSIZE_BYTES","524288000"),
        "--", *argv
    ]
    try:
        return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s, text=True)
    except subprocess.TimeoutExpired:
        raise_err("E_TIMEOUT", "sandbox timeout", retryable=True, evidence={"cmd": argv[:3]})
    except subprocess.CalledProcessError as e:
        raise_err("E_SANDBOX", f"sandboxed process failed: rc={e.returncode}", evidence={"cmd": argv[:3], "stderr": e.stderr[-512:]})

def copy_pkg_resource(rel: str, dst: str):
    from importlib.resources import files
    src = files("poi_invariants_pro").joinpath(rel)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(src.read_bytes())
