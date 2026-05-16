"""
lowkey ignore this because this is not a comprehensive demo
"""

from rng.qrng import qrng_bits, string_to_bits, bits_to_string, xor_bits
from functions.bob import measure_qubits, extract_key
from functions.eve import create_attack
import random


def run_bb84_with_eve(num_bits, eve_attack_type="none", seed=None):
    """
    Run BB84 protocol with Eve attempting to eavesdrop.
    
    Args:
        num_bits (int): Number of qubits to transmit
        eve_attack_type (str): Type of Eve's attack ('measure-and-resend', 'none', etc)
        seed (int): Random seed for reproducibility
    
    Returns:
        dict: Complete protocol results
    """
    if seed is not None:
        random.seed(seed)
    
    print("\n" + "="*60)
    print(f"BB84 PROTOCOL WITH EVE ({eve_attack_type} attack)")
    print("="*60)
    
    # ===== ALICE SIDE =====
    print("\n[ALICE]")
    print(f"1. Generating {num_bits} random bits and bases...")
    alice_bits_and_bases = qrng_bits(num_bits)
    alice_bits = [bit for bit, _ in alice_bits_and_bases]
    alice_bases = [basis for _, basis in alice_bits_and_bases]
    print(f"   - Alice's bits: {' '.join(str(b) for b in alice_bits[:16])}... (showing first 16)")
    print(f"   - Alice's bases: {' '.join(alice_bases[:16])}... (showing first 16)")
    
    # ===== EVE SIDE =====
    print("\n[EVE]")
    print(f"2. Eve attempting {eve_attack_type} attack...")
    eve = create_attack(eve_attack_type)
    eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)
    
    if eve_attack_type != "none":
        eve_correct_count = sum(1 for i in range(num_bits) if alice_bases[i] == eve_bases[i])
        print(f"   - Eve measured with correct basis: {eve_correct_count}/{num_bits} times")
        print(f"   - Eve bases: {' '.join(eve_bases[:16])}... (showing first 16)")
        print(f"   - Eve results: {' '.join(str(b) for b in eve_results[:16])}... (showing first 16)")
    else:
        print("   - No eavesdropping")
    
    # ===== BOB SIDE =====
    print("\n[BOB]")
    print(f"3. Bob measuring qubits in random bases...")
    bob_bases, bob_results = measure_qubits(alice_bits if eve_attack_type == "none" else forwarded_bits, 
                                            alice_bases, num_bits)
    print(f"   - Bob's bases: {' '.join(bob_bases[:16])}... (showing first 16)")
    print(f"   - Bob's results: {' '.join(str(b) for b in bob_results[:16])}... (showing first 16)")
    
    # ===== SIFT KEYS =====
    print("\n[SIFTING KEYS]")
    print(f"4. Alice and Bob publicly compare bases (keeping match indices secret)...")
    shared_key_alice, matching_indices = extract_key(alice_bits, alice_bases, bob_bases, bob_results)
    matching_count = len(matching_indices)
    print(f"   - Matching bases: {matching_count}/{num_bits} ({100*matching_count/num_bits:.1f}%)")
    print(f"   - Shared key length: {len(shared_key_alice)} bits")
    print(f"   - Alice's sifted key: {''.join(str(b) for b in shared_key_alice[:32])}... (first 32 bits)")
    
    # ===== EAVESDROPPING DETECTION =====
    print("\n[EAVESDROPPING DETECTION]")
    print(f"5. Alice and Bob test a subset of the shared key to detect eavesdropping...")
    
    if len(shared_key_alice) > 10:
        test_sample_size = max(1, len(shared_key_alice) // 4)
        test_indices = random.sample(range(len(shared_key_alice)), test_sample_size)
        alice_test_bits = [shared_key_alice[i] for i in test_indices]
        
        # Bob's corresponding bits (from his measurements)
        bob_sifted_key = [bob_results[idx] for idx in matching_indices]
        bob_test_bits = [bob_sifted_key[i] for i in test_indices]
        
        mismatches = sum(1 for a, b in zip(alice_test_bits, bob_test_bits) if a != b)
        mismatch_rate = mismatches / len(test_indices)
        
        print(f"   - Test sample size: {test_sample_size}")
        print(f"   - Mismatches found: {mismatches}/{test_sample_size} ({100*mismatch_rate:.1f}%)")
        
        eavesdrop_detected = mismatches > 0
        
        # Remove tested bits from final key
        final_key = [bit for i, bit in enumerate(shared_key_alice) if i not in test_indices]
        print(f"   - Eavesdropping detected: {'YES' if eavesdrop_detected else 'NO'}")
        print(f"   - Final secure key length: {len(final_key)} bits")
    else:
        eavesdrop_detected = False
        final_key = shared_key_alice
        print(f"   - Not enough bits for reliable test")
    
    return {
        'alice_bits': alice_bits,
        'alice_bases': alice_bases,
        'eve_bases': eve_bases,
        'eve_results': eve_results,
        'bob_bases': bob_bases,
        'bob_results': bob_results,
        'shared_key': final_key,
        'eavesdrop_detected': eavesdrop_detected,
        'eve_attack_type': eve_attack_type,
        'matching_count': matching_count
    }


def demo_encryption_with_eve(message, eve_attack_type="none"):
    """
    Demo: Alice sends encrypted message to Bob with Eve present.
    
    Args:
        message (str): Message to encrypt
        eve_attack_type (str): Type of Eve's attack
    """
    num_bits = 512  # Generate enough bits for encryption
    
    result = run_bb84_with_eve(num_bits, eve_attack_type)
    
    print("\n" + "="*60)
    print("MESSAGE ENCRYPTION/DECRYPTION")
    print("="*60)
    
    shared_key = result['shared_key']
    message_bits = string_to_bits(message)
    
    print(f"\n[MESSAGE ENCRYPTION]")
    print(f"Alice's message: '{message}'")
    print(f"Message length: {len(message)} characters")
    print(f"Message bits needed: {len(message_bits)} bits")
    print(f"Shared key available: {len(shared_key)} bits")
    
    if result['eavesdrop_detected']:
        print("\nEAVESDROPPING DETECTED!")
        print("Alice and Bob abort the protocol. Message NOT sent.")
        return
    
    if len(shared_key) < len(message_bits):
        print(f"\nNOT ENOUGH KEY! Need {len(message_bits)} bits, have {len(shared_key)}")
        print("Encryption aborted.")
        return
    
    print(f"\n[ENCRYPTION]")
    print(f"1. Alice converts message to binary: {' '.join(str(b) for b in message_bits[:32])}...")
    
    encrypted_bits = xor_bits(message_bits, shared_key)
    print(f"2. Alice XORs with shared key")
    print(f"   Encrypted bits: {' '.join(str(b) for b in encrypted_bits[:32])}...")
    
    print(f"\n[TRANSMISSION]")
    print(f"3. Alice sends encrypted message to Bob")
    
    print(f"\n[DECRYPTION]")
    print(f"4. Bob XORs encrypted bits with shared key")
    
    decrypted_bits = xor_bits(encrypted_bits, shared_key)
    decrypted_message = bits_to_string(decrypted_bits)
    
    print(f"   Decrypted bits: {' '.join(str(b) for b in decrypted_bits[:32])}...")
    print(f"5. Bob converts bits back to text: '{decrypted_message}'")
    
    # Verify
    if decrypted_message == message:
        print(f"\n✓ SUCCESS! Message correctly decrypted: '{decrypted_message}'")
    else:
        print(f"\n✗ FAILED! Message corrupted")
        print(f"Expected: '{message}'")
        print(f"Got: '{decrypted_message}'")


def compare_attack_types():
    """Compare different Eve attack types."""
    print("\n" + "="*70)
    print("COMPARING EVE ATTACK TYPES")
    print("="*70)
    
    attack_types = ["none", "measure-and-resend", "intercept-and-replace", "cloned-state"]
    
    for attack_type in attack_types:
        print(f"\n--- Attack: {attack_type} ---")
        result = run_bb84_with_eve(128, attack_type, seed=42)
        
        print(f"Result: {'Eavesdropping DETECTED' if result['eavesdrop_detected'] else 'No detection'}")
        print(f"Key length: {len(result['shared_key'])} bits")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("BB84 QUANTUM KEY DISTRIBUTION WITH EVE")
    print("="*70)
    
    # Demo 1: No Eve
    print("\n\n### SCENARIO 1: Normal operation (no eavesdropping) ###")
    demo_encryption_with_eve("Hello", eve_attack_type="none")
    
    # Demo 2: Eve attacks
    print("\n\n### SCENARIO 2: Eve performs measure-and-resend attack ###")
    demo_encryption_with_eve("Hello", eve_attack_type="measure-and-resend")
    
    # Demo 3: Compare attacks
    print("\n\n### SCENARIO 3: Comparing attack types ###")
    compare_attack_types()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
