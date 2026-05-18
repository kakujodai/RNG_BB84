from rng.qrng import string_to_bits, xor_bits
from functions.bb84 import bb84_protocol

# demonstrates whole workflow via using the bb84 to generate a shared key & gets the message
# to eventually encrypt, send and decrypt.

def alice_generate_and_encrypt(message, num_bits=64):
    """
    Alice runs BB84, generates a shared key, and encrypts her message.
    Returns: encrypted_bits, shared_key, message_bits
    """
    result = bb84_protocol(num_bits)
    # Unpack new return values
    shared_key, shared_indices, alice_bits, alice_bases, bob_bases, bob_results, eavesdrop_detected = result
    message_bits = string_to_bits(message)
    encrypted_bits = xor_bits(message_bits, shared_key)
    return encrypted_bits, shared_key, message_bits, eavesdrop_detected

def bob_decrypt(encrypted_bits, shared_key):
    from rng.qrng import bits_to_string
    decrypted_bits = xor_bits(encrypted_bits, shared_key)
    return bits_to_string(decrypted_bits)

if __name__ == "__main__":
    # Alice sends a message to Bob
    print("\n--- Quantum Key Distribution and Secure Messaging Demo ---\n")
    message = input("Enter Alice's message to Bob: ")
    print(f"\nStep 1: Alice wants to send: '{message}'")
    encrypted_bits, shared_key, message_bits, eavesdrop_detected = alice_generate_and_encrypt(message)
    print(f"Step 2: Alice converts her message to binary: {''.join(map(str, message_bits))}")
    if eavesdrop_detected:
        print("\nStep 3: Eavesdropping detected during BB84 key exchange! Key exchange aborted. No message sent.")
    else:
        print(f"\nStep 3: BB84 protocol completed. Shared secret key: {''.join(map(str, shared_key))}")
        print(f"Step 4: Alice encrypts the message bits with the shared key (XOR):\n         {''.join(map(str, message_bits))} (message)\n     XOR {''.join(map(str, shared_key))} (key)\n     =   {''.join(map(str, encrypted_bits))} (encrypted)")
        print(f"\nStep 5: Alice sends the encrypted bits to Bob: {''.join(map(str, encrypted_bits))}")
        print(f"Step 6: Bob decrypts the message using the shared key (XOR):\n         {''.join(map(str, encrypted_bits))} (encrypted)\n     XOR {''.join(map(str, shared_key))} (key)\n     =   {''.join(map(str, message_bits))} (decrypted bits)")
        decrypted_message = bob_decrypt(encrypted_bits, shared_key)
        print(f"\nStep 7: Bob converts the decrypted bits back to text: '{decrypted_message}'")
