"""
Presentation-focused BB84 demo.

What this script is optimized for:
    1) Show Alice's random bits/bases in terminal.
    2) Show what Eve intercepts and Eve accuracy.
    3) Show what Bob receives/measures.
    4) Build shared key and run eavesdropping check.
    5) Prompt for Alice message, then encrypt/decrypt.
    6) Compare attacks under QRNG vs PRNG-like generation.

Note: This uses simulator-based quantum randomness from qrng.py.
"""

import random

from functions.bob import measure_qubit
from functions.eve import create_attack
from rng.qrng import qrng_bits, string_to_bits, bits_to_string, xor_bits


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
    print("\n" + "=" * 74) # just a visual separator for presentation clarity
    print("BB84 LIVE PRESENTATION DEMO")
    print("=" * 74)

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

    result = _run_once(
        num_bits=num_bits,
        attack_type=attack,
        random_mode=random_mode,
        prng_seed=prng_seed,
    )

    print("\n[ALICE] Random generation")
    print(f"- Alice bits (first 24):   {_fmt_first(result['alice_bits'], 24)}")
    print(f"- Alice bases (first 24):  {_fmt_first(result['alice_bases'], 24)}")

    print("\n[EVE] Intercept/read summary")
    if attack == "none":
        print("- No attack selected.")
    else:
        print(f"- Eve bases (first 24):     {_fmt_first(result['eve_bases'], 24)}")
        print(f"- Eve read bits (first 24): {_fmt_first(result['eve_results'], 24)}")
        print(f"- Eve basis accuracy:       {100 * result['eve_basis_accuracy']:.2f}%")
        print(f"- Eve bit-read accuracy:    {100 * result['eve_bit_accuracy']:.2f}%")

    print("\n[CHANNEL -> BOB] What Bob receives")
    print(f"- Transmitted bits (first 24):  {_fmt_first(result['transmitted_bits'], 24)}")
    print(f"- Transmitted bases (first 24): {_fmt_first(result['transmitted_bases'], 24)}")

    print("\n[BOB] Measurement summary")
    print(f"- Bob bases (first 24):      {_fmt_first(result['bob_bases'], 24)}")
    print(f"- Bob measured bits (first 24): {_fmt_first(result['bob_results'], 24)}")

    print("\n[SIFT + TEST]")
    print(f"- Basis matches: {len(result['matching_indices'])}/{num_bits}")
    print(f"- Sifted key length: {len(result['alice_sifted'])}")
    print(f"- Test sample size: {result['sample_size']}")
    print(f"- Test mismatches: {result['mismatches']}")
    print(f"- Eavesdrop detected: {'YES' if result['eavesdrop_detected'] else 'NO'}")
    print(f"- Final key length: {len(result['final_key'])}")

    message = input("\nEnter Alice message to encrypt: ") # hello bob or wahtever
    message_bits = string_to_bits(message)
    print(f"- Message bits: {_fmt_first(message_bits, 64)}")

    if result["eavesdrop_detected"]:
        print("\nEncryption aborted because eavesdropping was detected.")
        return

    if not result["final_key"]:
        print("\nEncryption aborted because final key is empty.")
        return

    encrypted_bits = xor_bits(message_bits, result["final_key"])
    decrypted_bits = xor_bits(encrypted_bits, result["final_key"])
    decrypted_message = bits_to_string(decrypted_bits)

    print("\n[ENCRYPTION/DECRYPTION]")
    print(f"- Encrypted bits: {_fmt_first(encrypted_bits, 64)}")
    print(f"- Bob decrypted message: {decrypted_message}")


def run_comparison_matrix():
    print("\n" + "=" * 74)
    print("QRNG VS PRNG COMPARISON ACROSS EVE ATTACKS")
    print("=" * 74)

    num_bits = int((input("Bits per trial [128]: ").strip() or "128"))
    trials = int((input("Trials per attack [6]: ").strip() or "6"))

    print("\nThis will run attack comparisons for:")
    print("- Random mode: qrng")
    print("- Random mode: prng")
    print("- Optional PRNG compromised-seed scenario (Eve predicts Alice bases)")

    use_compromised = (
        input("Include compromised PRNG scenario? [y/N]: ").strip().lower() == "y"
    )

    for random_mode in ["qrng", "prng"]:
        print("\n" + "-" * 74)
        print(f"Random mode: {random_mode.upper()}")
        print("Attack | Detect Rate | Eve Basis Acc | Eve Bit Acc | Avg Final Key")

        for attack in ATTACKS:
            detected_count = 0
            basis_acc = []
            bit_acc = []
            key_lengths = []

            for trial in range(trials):
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

            detect_rate = detected_count / trials
            avg_key_len = sum(key_lengths) / len(key_lengths)
            avg_basis = (sum(basis_acc) / len(basis_acc)) if basis_acc else None
            avg_bit = (sum(bit_acc) / len(bit_acc)) if bit_acc else None

            basis_text = "N/A" if avg_basis is None else f"{100 * avg_basis:6.2f}%"
            bit_text = "N/A" if avg_bit is None else f"{100 * avg_bit:6.2f}%"
            print(
                f"{attack:20s} | {100 * detect_rate:9.2f}% | {basis_text:12s} | {bit_text:10s} | {avg_key_len:11.1f}"
            )

        if random_mode == "prng" and use_compromised:
            print("\nCompromised PRNG seed scenario (presentation contrast):")
            print("Attack | Detect Rate | Eve Basis Acc | Eve Bit Acc | Avg Final Key")
            for attack in ATTACKS:
                detected_count = 0
                basis_acc = []
                bit_acc = []
                key_lengths = []

                for trial in range(trials):
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

                detect_rate = detected_count / trials
                avg_key_len = sum(key_lengths) / len(key_lengths)
                avg_basis = (sum(basis_acc) / len(basis_acc)) if basis_acc else None
                avg_bit = (sum(bit_acc) / len(bit_acc)) if bit_acc else None

                basis_text = "N/A" if avg_basis is None else f"{100 * avg_basis:6.2f}%"
                bit_text = "N/A" if avg_bit is None else f"{100 * avg_bit:6.2f}%"
                print(
                    f"{attack:20s} | {100 * detect_rate:9.2f}% | {basis_text:12s} | {bit_text:10s} | {avg_key_len:11.1f}"
                )

    print("\nInterpretation:")
    print("- In normal attacks, Eve's basis guess is near 50%, so her read accuracy is limited.")
    print("- Detection rates stay non-zero because wrong-basis Eve measurements introduce errors.")
    print("- If PRNG seed is compromised, Eve can predict bases and become much more accurate.")
    print("- That contrast is what supports the QRNG security argument in your presentation.")


def main():
    print("\nChoose mode:")
    print("1) Live step-by-step demo")
    print("2) QRNG vs PRNG attack comparison matrix")
    choice = (input("Enter 1 or 2 [1]: ").strip() or "1")

    if choice == "2":
        run_comparison_matrix()
    else:
        run_live_demo()


if __name__ == "__main__":
    main()
