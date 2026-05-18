"""
Presentation-focused BB84 demo.

What this script is optimized for:
    1) Show Alice's random bits/bases in terminal.
    2) Show what Eve intercepts and Eve accuracy.
    3) Show what Bob receives/measures.
    4) Build shared key and run eavesdropping check.
    5) Prompt for Alice message, then encrypt/decrypt.
    6) Compare attacks under QRNG vs PRNG-like generation.

Note: QRNG mode uses real IBM quantum hardware through Qiskit Runtime.
"""

import random
import os
from pathlib import Path

import logging
import sys
from io import StringIO

# Suppress IBM service logs
logging.getLogger('qiskit_ibm_runtime').setLevel(logging.ERROR)

# Create a StringIO buffer to capture all output
output_buffer = StringIO()

env_path = Path(__file__).parent / '.env'

if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
        content = f.read()
    
    for line in content.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            os.environ[key] = value
else:
    print(f"ERROR: .env file not found at {env_path}")

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler


def write_results_to_file(results, filename="results/simulation_output.txt"):
    """Write simulation results to a text file."""
    with open(filename, "w") as f:
        f.write(results)

def print_to_buffer(*args, **kwargs):
    """Print to the output buffer instead of terminal."""
    print(*args, **kwargs, file=output_buffer)
    print(*args, **kwargs)

def save_buffer_to_file(filename="results/simulation_output.txt"):
    """Save the buffered output to a file."""
    with open(filename, "w") as f:
        f.write(output_buffer.getvalue())


def _get_ibm_backend(backend_name="ibm_kingston"):
    """Connect to IBM Quantum using IBM_TOKEN and return a real backend."""
    token = os.getenv("IBM_TOKEN")

    if token is None:
        raise ValueError(
            "IBM_TOKEN is not set."
        )

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
    )

    return service.backend(backend_name)


def _real_quantum_random_bitstring(num_random_bits, backend_name="ibm_kingston"):
    """Generate num_random_bits from a real IBM quantum backend."""
    if num_random_bits <= 0:
        return ""

    backend = _get_ibm_backend(backend_name)

    #use at most the backend's available qubits per circuit. If we need more
    #random bits than that, submit several circuits in one sampler job.
    max_qubits = min(num_random_bits, getattr(backend, "num_qubits", num_random_bits))

    circuits = []
    bits_left = num_random_bits

    while bits_left > 0:
        n = min(max_qubits, bits_left)
        circuit = QuantumCircuit(n, n)
        circuit.h(range(n))
        circuit.measure(range(n), range(n))
        circuits.append(circuit)
        bits_left -= n

    pm = generate_preset_pass_manager(
        backend=backend,
        optimization_level=1,
    )

    isa_circuits = [pm.run(circuit) for circuit in circuits]

    sampler = Sampler(mode=backend)
    job = sampler.run(isa_circuits, shots=1)

    # Job submission message removed to keep terminal clean
    # print(f"IBM Quantum job submitted: {job.job_id()}")
    
    # Show progress indicator on terminal
    import sys
    sys.__stdout__.write(".")
    sys.__stdout__.flush()

    result = job.result()

    bitstring = ""
    for pub_result in result:
        bitstring += pub_result.data.c.get_bitstrings()[0]

    return bitstring[:num_random_bits]


def qrng_bits(num_bits, backend_name="ibm_kingston"):
    """
    Return [(bit, basis), ...] using real IBM quantum randomness.

    Each BB84 position needs two random values:
      1) Alice/Bob's data bit: 0 or 1
      2) Alice/Bob's basis: Z or X
    """
    raw_bits = _real_quantum_random_bitstring(2 * num_bits, backend_name)

    pairs = []
    for i in range(num_bits):
        bit = int(raw_bits[2 * i])
        basis = "Z" if raw_bits[2 * i + 1] == "0" else "X"
        pairs.append((bit, basis))

    return pairs


from functions.bob import measure_qubit
from functions.eve import create_attack
from rng.qrng import string_to_bits, bits_to_string, xor_bits


ATTACKS = ["none", "measure-and-resend", "intercept-and-replace", "cloned-state"]


def _generate_alice_bits_and_bases(num_bits, random_mode="qrng", prng_seed=42):
    if random_mode == "qrng":
        pairs = qrng_bits(num_bits)
        bits = [bit for bit, _ in pairs]
        bases = [basis for _, basis in pairs]
        return bits, bases

    rng = random.Random(prng_seed)
    bits = [rng.randint(0, 1) for _ in range(num_bits)]
    bases = ["Z" if rng.randint(0, 1) == 0 else "X" for _ in range(num_bits)]
    return bits, bases


def _generate_bob_bases(num_bits, random_mode="qrng", prng_seed=99):
    if random_mode == "qrng":
        return [basis for _, basis in qrng_bits(num_bits)]

    rng = random.Random(prng_seed)
    return ["Z" if rng.randint(0, 1) == 0 else "X" for _ in range(num_bits)]


def _fmt_first(values, n=24):
    head = values[:n]
    tail = "..." if len(values) > n else ""
    return " ".join(str(v) for v in head) + tail


def _run_once(
    num_bits,
    attack_type,
    random_mode="qrng",
    prng_seed=42, # only used if random_mode is "prng"
    sample_ratio=0.25, # fraction of sifted key to use for eavesdrop test
    force_prng_seed_compromise=False,
):
    alice_bits, alice_bases = _generate_alice_bits_and_bases(num_bits, random_mode, prng_seed)

    eve = create_attack(attack_type)
    eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)

    # if PRNG seed is compromised, Eve predicts Alice bases perfectly.
    if force_prng_seed_compromise and random_mode == "prng" and attack_type != "none":
        eve_bases = list(alice_bases)
        eve_results = list(alice_bits)
        forwarded_bits = list(alice_bits)

    if attack_type == "none":
        transmitted_bits = list(alice_bits)
        transmitted_bases = list(alice_bases)
    else:
        transmitted_bits = list(forwarded_bits) # Eve may have changed some bits if attack is not "none"
        transmitted_bases = list(eve_bases)

    bob_bases = _generate_bob_bases(num_bits, random_mode, prng_seed + 1)
    bob_results = [
        measure_qubit(transmitted_bits[i], transmitted_bases[i], bob_bases[i])
        for i in range(num_bits)
    ]

    matching_indices = [i for i in range(num_bits) if alice_bases[i] == bob_bases[i]]  # indices where bases match
    alice_sifted = [alice_bits[i] for i in matching_indices]                           # sifted key bits for Alice
    bob_sifted = [bob_results[i] for i in matching_indices]                            # sifted key bits for Bob

    if alice_sifted: 
        sample_size = max(1, int(len(alice_sifted) * sample_ratio))
        sample_size = min(sample_size, len(alice_sifted))
        sample_indices = random.sample(range(len(alice_sifted)), sample_size)
        mismatches = sum(1 for i in sample_indices if alice_sifted[i] != bob_sifted[i])
        eavesdrop_detected = mismatches > 0
        final_key = [bit for i, bit in enumerate(alice_sifted) if i not in sample_indices] # final key after removing test sample
    else:
        sample_size = 0
        mismatches = 0
        eavesdrop_detected = False
        final_key = []

    if attack_type == "none": # Eve has no info, so accuracy is not applicable for resulst
        eve_bit_accuracy = None
        eve_basis_accuracy = None
    else:
        eve_bit_accuracy = sum(1 for a, e in zip(alice_bits, eve_results) if a == e) / num_bits
        eve_basis_accuracy = sum(1 for a, e in zip(alice_bases, eve_bases) if a == e) / num_bits

    results_summary = f"Attack: {attack_type}\n"
    results_summary += f"Random Mode: {random_mode}\n"
    results_summary += f"Bits: {num_bits}\n"
    results_summary += f"Eavesdrop Detected: {eavesdrop_detected}\n"
    results_summary += f"Alice Sifted Key: {alice_sifted}\n"
    results_summary += f"Bob Sifted Key: {bob_sifted}\n"

    print_to_buffer(results_summary)

    return { # god bro
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "eve_bases": eve_bases,
        "eve_results": eve_results,
        "forwarded_bits": forwarded_bits,
        "transmitted_bits": transmitted_bits,
        "transmitted_bases": transmitted_bases,
        "bob_bases": bob_bases,
        "bob_results": bob_results,
        "matching_indices": matching_indices,
        "alice_sifted": alice_sifted,
        "bob_sifted": bob_sifted,
        "sample_size": sample_size,
        "mismatches": mismatches,
        "eavesdrop_detected": eavesdrop_detected,
        "final_key": final_key,
        "eve_bit_accuracy": eve_bit_accuracy,
        "eve_basis_accuracy": eve_basis_accuracy,
    }


def run_live_demo():
    print_to_buffer("\n" + "=" * 74) # just a visual separator for presentation clarity
    print_to_buffer("BB84 LIVE PRESENTATION DEMO")
    print_to_buffer("=" * 74)

    num_bits_text = input("\nEnter number of photons/bits to send: ").strip() or "128" # note we only show the first 24 bits/bases later
    num_bits = int(num_bits_text)

    random_mode = (
        input("Randomness type? AKA qrng or prng [qrng]: ").strip().lower()
        or "qrng"
    )
    if random_mode not in {"qrng", "prng"}:
        random_mode = "qrng"

    attack = (
        input(
            "Choose Eve attack [none | measure-and-resend | intercept-and-replace | cloned-state] [measure-and-resend]: " 
        ).strip().lower()
        or "measure-and-resend"
    )
    if attack not in ATTACKS:
        attack = "measure-and-resend"

    prng_seed = 42 # hardcode seed for PRNG mode, can be overridden by user input
    if random_mode == "prng":
        seed_text = input("Enter PRNG seed [hardcoded as 42]: ").strip() or "42"
        prng_seed = int(seed_text)

    if random_mode == "qrng":
        print("Generating quantum random numbers", end="", flush=True)
    
    result = _run_once(
        num_bits=num_bits,
        attack_type=attack,
        random_mode=random_mode,
        prng_seed=prng_seed,
    )
    
    if random_mode == "qrng":
        print(" ✓")

    print_to_buffer("\n[ALICE] Random generation")
    print_to_buffer(f"- Alice bits (first 24):   {_fmt_first(result['alice_bits'], 24)}")
    print_to_buffer(f"- Alice bases (first 24):  {_fmt_first(result['alice_bases'], 24)}")

    print_to_buffer("\n[EVE] Intercept/read summary")
    if attack == "none":
        print_to_buffer("- No attack selected.")
    else:
        print_to_buffer(f"- Eve bases (first 24):     {_fmt_first(result['eve_bases'], 24)}")
        print_to_buffer(f"- Eve read bits (first 24): {_fmt_first(result['eve_results'], 24)}")
        print_to_buffer(f"- Eve basis accuracy:       {100 * result['eve_basis_accuracy']:.2f}%")
        print_to_buffer(f"- Eve bit-read accuracy:    {100 * result['eve_bit_accuracy']:.2f}%")

    print_to_buffer("\n[CHANNEL -> BOB] What Bob receives")
    print_to_buffer(f"- Transmitted bits (first 24):  {_fmt_first(result['transmitted_bits'], 24)}")
    print_to_buffer(f"- Transmitted bases (first 24): {_fmt_first(result['transmitted_bases'], 24)}")

    print_to_buffer("\n[BOB] Measurement summary")
    print_to_buffer(f"- Bob bases (first 24):      {_fmt_first(result['bob_bases'], 24)}")
    print_to_buffer(f"- Bob measured bits (first 24): {_fmt_first(result['bob_results'], 24)}")

    print_to_buffer("\n[SIFT + TEST]")
    print_to_buffer(f"- Basis matches: {len(result['matching_indices'])}/{num_bits}")
    print_to_buffer(f"- Sifted key length: {len(result['alice_sifted'])}")
    print_to_buffer(f"- Test sample size: {result['sample_size']}")
    print_to_buffer(f"- Test mismatches: {result['mismatches']}")
    print_to_buffer(f"- Eavesdrop detected: {'YES' if result['eavesdrop_detected'] else 'NO'}")
    print_to_buffer(f"- Final key length: {len(result['final_key'])}")

    message = input("\nEnter Alice message to encrypt: ") # hello bob or wahtever
    message_bits = string_to_bits(message)
    print_to_buffer(f"- Message bits: {_fmt_first(message_bits, 64)}")

    if result["eavesdrop_detected"]:
        print_to_buffer("\nEncryption aborted because eavesdropping was detected.")
        return

    if not result["final_key"]:
        print_to_buffer("\nEncryption aborted because final key is empty.")
        return

    encrypted_bits = xor_bits(message_bits, result["final_key"])
    decrypted_bits = xor_bits(encrypted_bits, result["final_key"])
    decrypted_message = bits_to_string(decrypted_bits)

    print_to_buffer("\n[ENCRYPTION/DECRYPTION]")
    print_to_buffer(f"- Encrypted bits: {_fmt_first(encrypted_bits, 64)}")
    print_to_buffer(f"- Bob decrypted message: {decrypted_message}")


def run_comparison_matrix():
    print_to_buffer("\n" + "=" * 74)
    print_to_buffer("QRNG VS PRNG COMPARISON ACROSS EVE ATTACKS")
    print_to_buffer("=" * 74)

    num_bits = int((input("Bits per trial [128]: ").strip() or "128"))
    trials = int((input("Trials per attack [6]: ").strip() or "6"))

    print_to_buffer("\nThis will run attack comparisons for:")
    print_to_buffer("- Random mode: qrng")
    print_to_buffer("- Random mode: prng")
    print_to_buffer("- Optional PRNG compromised-seed scenario (Eve predicts Alice bases)")

    use_compromised = (
        input("Include compromised PRNG scenario? [y/N]: ").strip().lower() == "y"
    )

    for random_mode in ["qrng", "prng"]:
        print_to_buffer("\n" + "-" * 74)
        print_to_buffer(f"Random mode: {random_mode.upper()}")
        print_to_buffer("Attack | Detect Rate % | Eve Basis Acc % | Eve Bit Acc %| Avg Final Key")

        for attack in ATTACKS:
            detected_count = 0
            basis_acc = []
            bit_acc = []
            key_lengths = []

            print(f"  Processing {attack} attack (mode: {random_mode})...", end="", flush=True)
            
            for trial in range(trials):
                print(".", end="", flush=True)  # progression indicator
                result = _run_once(
                    num_bits=num_bits,
                    attack_type=attack,
                    random_mode=random_mode,
                    prng_seed=42 + trial,
                    force_prng_seed_compromise=False,
                )
                detected_count += int(result["eavesdrop_detected"])
                key_lengths.append(len(result["final_key"]))
                if result["eve_basis_accuracy"] is not None:
                    basis_acc.append(result["eve_basis_accuracy"])
                    bit_acc.append(result["eve_bit_accuracy"])

            print(" ✓")  # checkamrk for finish

            detect_rate = detected_count / trials
            avg_key_len = sum(key_lengths) / len(key_lengths)
            avg_basis = (sum(basis_acc) / len(basis_acc)) if basis_acc else None
            avg_bit = (sum(bit_acc) / len(bit_acc)) if bit_acc else None

            basis_text = "N/A" if avg_basis is None else f"{100 * avg_basis:6.2f}%"
            bit_text = "N/A" if avg_bit is None else f"{100 * avg_bit:6.2f}%"
            print_to_buffer(
                f"{attack:20s} | {100 * detect_rate:9.2f}% | {basis_text:12s} | {bit_text:10s} | {avg_key_len:11.1f}"
            )

        if random_mode == "prng" and use_compromised:
            print_to_buffer("\nCompromised PRNG seed scenario (presentation contrast):")
            print_to_buffer("Attack | Detect Rate | Eve Basis Acc | Eve Bit Acc | Avg Final Key")
            for attack in ATTACKS:
                detected_count = 0
                basis_acc = []
                bit_acc = []
                key_lengths = []

                print(f"  Processing {attack} attack (compromised seed)...", end="", flush=True)
                
                for trial in range(trials):
                    print(".", end="", flush=True)
                    result = _run_once(
                        num_bits=num_bits,
                        attack_type=attack,
                        random_mode="prng",
                        prng_seed=42 + trial,
                        force_prng_seed_compromise=True,
                    )
                    detected_count += int(result["eavesdrop_detected"])
                    key_lengths.append(len(result["final_key"]))
                    if result["eve_basis_accuracy"] is not None:
                        basis_acc.append(result["eve_basis_accuracy"])
                        bit_acc.append(result["eve_bit_accuracy"])

                print(" ✓")

                detect_rate = detected_count / trials
                avg_key_len = sum(key_lengths) / len(key_lengths)
                avg_basis = (sum(basis_acc) / len(basis_acc)) if basis_acc else None
                avg_bit = (sum(bit_acc) / len(bit_acc)) if bit_acc else None

                basis_text = "N/A" if avg_basis is None else f"{100 * avg_basis:6.2f}%"
                bit_text = "N/A" if avg_bit is None else f"{100 * avg_bit:6.2f}%"
                print_to_buffer(
                    f"{attack:20s} | {100 * detect_rate:9.2f}% | {basis_text:12s} | {bit_text:10s} | {avg_key_len:11.1f}"
                )

def main():
    print("\nChoose mode:")
    print("1) step-by-step demo")
    print("2) QRNG vs PRNG comparison")
    choice = (input("Enter 1 or 2 [1]: ").strip() or "1")

    if choice == "2":
        run_comparison_matrix()
    else:
        run_live_demo()
    
    save_buffer_to_file("results/simulation_output.txt")
    print("\nResults saved to: results/simulation_output.txt")


if __name__ == "__main__":
    main()
