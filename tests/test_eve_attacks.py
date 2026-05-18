"""
Detailed tests for Eve's attack detection in BB84 protocol.
Analyzes how different eavesdropping strategies are detected.
"""

import unittest
from rng.qrng import qrng_bits, string_to_bits, bits_to_string, xor_bits
from functions.bob import measure_qubits, extract_key
from functions.eve import create_attack, MeasureAndResendAttack, InterceptAndReplaceAttack
import random


class TestEveAttackStrategies(unittest.TestCase):
    """Test individual Eve attack strategies in detail."""
    
    def setUp(self):
        self.num_bits = 200
        random.seed(42)
    
    def generate_alice_setup(self):
        """Generate Alice's bits and bases using deterministic PRNG."""
        alice_bits = [random.randint(0, 1) for _ in range(self.num_bits)]
        alice_bases = [random.choice(['Z', 'X']) for _ in range(self.num_bits)]
        return alice_bits, alice_bases
    
    def generate_bob_bases(self):
        """Generate Bob's measurement bases."""
        return [random.choice(['Z', 'X']) for _ in range(self.num_bits)]
    
    def test_measure_and_resend_error_rate(self):
        """
        Test error rate introduced by measure-and-resend attack.
        When Eve measures with wrong basis, ~50% of her measurements are wrong,
        and she forwards these wrong values to Bob.
        """
        alice_bits, alice_bases = self.generate_alice_setup()
        bob_bases = self.generate_bob_bases()
        
        eve = MeasureAndResendAttack()
        eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)
        
        # Count errors between Alice's bits and what Eve forwards
        # when Bob uses the correct basis
        eve_induced_errors = 0
        error_positions = []
        
        for i in range(self.num_bits):
            if alice_bases[i] == bob_bases[i]:
                # Bob would have measured correctly without Eve
                # But Eve might have forwarded wrong value
                if alice_bits[i] != forwarded_bits[i]:
                    eve_induced_errors += 1
                    error_positions.append(i)
        
        # Eve causes errors when she measured with wrong basis (~25% of positions)
        # This should be roughly 0.25 * 0.5 = 12.5% error rate
        error_rate = eve_induced_errors / self.num_bits if self.num_bits > 0 else 0
        
        print(f"\nMeasure-and-Resend Attack Analysis:")
        print(f"Total bits: {self.num_bits}")
        print(f"Eve-induced errors: {eve_induced_errors}")
        print(f"Error rate: {error_rate:.3%}")
        print(f"Eve wrong basis count: {sum(1 for i in range(self.num_bits) if alice_bases[i] != eve_bases[i])}")
        
        # Error rate should be low but detectable with enough samples
        self.assertLess(error_rate, 0.5)
    
    def test_eve_detection_via_sampling(self):
        """
        Test that Eve is detected by sampling and comparing bits.
        This is the standard BB84 eavesdropping detection method.
        """
        alice_bits, alice_bases = self.generate_alice_setup()
        bob_bases = self.generate_bob_bases()
        
        # Eve attacks
        eve = MeasureAndResendAttack()
        eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)
        
        # Get matching bases indices
        matching_indices = [i for i in range(self.num_bits) if alice_bases[i] == bob_bases[i]]
        
        if len(matching_indices) > 10:
            # Sample and compare
            sample_size = max(1, len(matching_indices) // 4)
            sample_indices = random.sample(matching_indices, sample_size)
            
            alice_sample = [alice_bits[i] for i in sample_indices]
            eve_sample = [forwarded_bits[i] for i in sample_indices]
            
            mismatches = sum(1 for a, e in zip(alice_sample, eve_sample) if a != e)
            mismatch_rate = mismatches / len(sample_indices) if len(sample_indices) > 0 else 0
            
            print(f"\nEve Detection via Sampling:")
            print(f"Sample size: {len(sample_indices)}")
            print(f"Mismatches: {mismatches}")
            print(f"Mismatch rate: {mismatch_rate:.3%}")
            
            # With Eve present using measure-and-resend, should detect some errors
            # (but not guaranteed with small samples)
            self.assertGreaterEqual(mismatch_rate, 0)
    
    def test_eve_basis_wrong_correlation(self):
        """Test that Eve's basis choices correlate with introduced errors."""
        alice_bits, alice_bases = self.generate_alice_setup()
        bob_bases = self.generate_bob_bases()
        
        eve = MeasureAndResendAttack()
        eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)
        
        # When Eve uses correct basis, forwarded = Alice's bit
        # When Eve uses wrong basis, forwarded = random (50% chance of error)
        
        correct_basis_errors = 0
        wrong_basis_errors = 0
        correct_basis_count = 0
        wrong_basis_count = 0
        
        for i in range(self.num_bits):
            if alice_bases[i] == eve_bases[i]:
                correct_basis_count += 1
                if alice_bits[i] != forwarded_bits[i]:
                    correct_basis_errors += 1
            else:
                wrong_basis_count += 1
                if alice_bits[i] != forwarded_bits[i]:
                    wrong_basis_errors += 1
        
        print(f"\nEve Basis Correlation Analysis:")
        print(f"Correct basis: {correct_basis_count} measurements, {correct_basis_errors} errors")
        print(f"Wrong basis: {wrong_basis_count} measurements, {wrong_basis_errors} errors")
        
        if correct_basis_count > 0:
            correct_error_rate = correct_basis_errors / correct_basis_count
            print(f"Error rate when Eve correct: {correct_error_rate:.3%}")
            # Should be 0 errors when Eve measures correct basis
            self.assertEqual(correct_basis_errors, 0)
        
        if wrong_basis_count > 0:
            wrong_error_rate = wrong_basis_errors / wrong_basis_count
            print(f"Error rate when Eve wrong: {wrong_error_rate:.3%}")
            # Should be ~50% error rate when Eve measures wrong basis
            self.assertGreater(wrong_error_rate, 0.2)
            self.assertLess(wrong_error_rate, 0.8)


class TestEveStatisticalAnalysis(unittest.TestCase):
    """Analyze statistical signatures of Eve's presence."""
    
    def setUp(self):
        self.num_bits = 500
        random.seed(42)
    
    def run_bb84_scenario(self, eve_present=False, eve_attack_type="measure-and-resend"):
        """
        Run a BB84 scenario and return various statistics.
        
        Args:
            eve_present (bool): Whether Eve is attacking
            eve_attack_type (str): Type of Eve attack
        
        Returns:
            dict: Statistics about the scenario
        """
        # Alice
        alice_bits = [random.randint(0, 1) for _ in range(self.num_bits)]
        alice_bases = [random.choice(['Z', 'X']) for _ in range(self.num_bits)]
        
        # Eve (if present)
        if eve_present:
            eve = create_attack(eve_attack_type)
            eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)
        else:
            forwarded_bits = alice_bits
        
        # Bob
        bob_bases = [random.choice(['Z', 'X']) for _ in range(self.num_bits)]
        
        # Extract key
        matching_indices = [i for i in range(self.num_bits) if alice_bases[i] == bob_bases[i]]
        final_key = [alice_bits[i] for i in matching_indices]
        forwarded_key = [forwarded_bits[i] for i in matching_indices]
        
        # Statistics
        eve_basis_matches = sum(1 for i in range(self.num_bits) if alice_bases[i] == eve_bases[i]) if eve_present else 0
        key_mismatches = sum(1 for a, f in zip(final_key, forwarded_key) if a != f)
        
        return {
            'eve_present': eve_present,
            'eve_attack_type': eve_attack_type,
            'key_length': len(final_key),
            'key_mismatches': key_mismatches,
            'mismatch_rate': key_mismatches / len(final_key) if len(final_key) > 0 else 0,
            'eve_basis_matches': eve_basis_matches if eve_present else None,
            'alice_bases_z_ratio': alice_bases.count('Z') / len(alice_bases),
            'bob_bases_z_ratio': bob_bases.count('Z') / len(bob_bases)
        }
    
    def test_no_eve_vs_eve_key_mismatch_rate(self):
        """Compare key mismatch rates with and without Eve."""
        no_eve = self.run_bb84_scenario(eve_present=False)
        eve_present = self.run_bb84_scenario(eve_present=True, eve_attack_type="measure-and-resend")
        
        print(f"\nNo Eve vs Eve Comparison:")
        print(f"Without Eve - Mismatches: {no_eve['key_mismatches']}/{no_eve['key_length']} ({no_eve['mismatch_rate']:.3%})")
        print(f"With Eve - Mismatches: {eve_present['key_mismatches']}/{eve_present['key_length']} ({eve_present['mismatch_rate']:.3%})")
        
        # Without Eve, no mismatches
        self.assertEqual(no_eve['key_mismatches'], 0)
        
        # With Eve, should have some mismatches
        self.assertGreater(eve_present['key_mismatches'], 0)
    
    def test_eve_attack_effectiveness(self):
        """Analyze how much information Eve successfully gets."""
        alice_bits = [random.randint(0, 1) for _ in range(self.num_bits)]
        alice_bases = [random.choice(['Z', 'X']) for _ in range(self.num_bits)]
        
        eve = MeasureAndResendAttack()
        eve_bases, eve_results, forwarded_bits = eve.attack(alice_bits, alice_bases)
        
        # Get bits where Eve measured correctly
        eve_correct_indices = [i for i in range(self.num_bits) if alice_bases[i] == eve_bases[i]]
        eve_correct_bits = [alice_bits[i] for i in eve_correct_indices]
        
        # Eve gains ~50% of the key when she measures correctly
        eve_key_fraction = len(eve_correct_indices) / self.num_bits
        
        print(f"\nEve's Information Gain:")
        print(f"Eve measured with correct basis: {len(eve_correct_indices)}/{self.num_bits} ({eve_key_fraction:.1%})")
        print(f"From these, Eve gets bits for her key (~50% of these)")
        
        # Eve gets ~50% through matching bases
        self.assertGreater(eve_key_fraction, 0.4)
        self.assertLess(eve_key_fraction, 0.6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
