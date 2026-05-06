from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager #translator to IBM quantum computer language for H gate
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler #logging into IBM computers online, sampler = "run this circuit lots of times and return measurement results"
import os

def make_rng_circuit(n: int):
    circuit = QuantumCircuit(n, n) #(qubits, classical bits) need classical bits to store measurements
    circuit.h(range(n)) #wont know if we're 0 or 1 until measured, true randomness babey
    circuit.measure(range(n), range(n))
    return circuit

token = os.getenv("IBM_TOKEN") #cant put API key in public repo... im stupid

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=token #api key
)

backend = service.backend("ibm_kingston") #picked one of the available quantum computers on the site

circuit = make_rng_circuit(1) #call the function

pm = generate_preset_pass_manager( #need this for hadamard
    backend=backend,
    optimization_level=1
)

isa_circuit = pm.run(circuit)

sampler = Sampler(mode=backend) #tell the sampler to work with backend, sampler runs the circuit and collects measurements
job = sampler.run([isa_circuit], shots=1) #one measurement = one random output

result = job.result()
bitstrings = result[0].data.c.get_bitstrings() #measurement results stored here

print(bitstrings[0])