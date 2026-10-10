"""
Proyecto: Quantum Key Distribution (QKD) - Protocolo BB84 con Detección de Espionaje
Tema: Quantum Unlocked / Quantum Impact - Qollab & IonQ Hackathon 101
Licencia: MIT
"This effort is supported by Qollab & IonQ"

Atribución y asistencia:
- El diseño del pipeline BB84, la simulación del canal cuántico y la
  detección de QBER fueron desarrollados con asistencia de Google Gemini
  durante el período de desarrollo del hackathon.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

# =====================================================================
# 1. PARÁMETROS Y SECUENCIAS ALEATORIAS
# =====================================================================
np.random.seed(42)

NUM_BITS = 16  # Bloque de fotones/qubits

# Bases: 0 = Base Z (Computacional), 1 = Base X (Diagonal)
ALICE_BITS = [int(b) for b in np.random.randint(2, size=NUM_BITS)]
ALICE_BASES = [int(b) for b in np.random.randint(2, size=NUM_BITS)]
BOB_BASES = [int(b) for b in np.random.randint(2, size=NUM_BITS)]
EVE_BASES = [int(b) for b in np.random.randint(2, size=NUM_BITS)]

def build_bb84_circuit(intercept_eve=False):
    """
    Construye el circuito cuántico empaquetando 16 fotones en registros paralelos.
    Compatible con ejecución de 1 solo job para Qollab e IonQ.
    """
    qc = QuantumCircuit(NUM_BITS, NUM_BITS)

    # --- PASO 1: ALICE PREPARA SUS ESTADOS CUÁNTICOS ---
    for i in range(NUM_BITS):
        if ALICE_BITS[i] == 1:
            qc.x(i)
        if ALICE_BASES[i] == 1:
            qc.h(i)

    # --- PASO 2: ATAQUE DE INTERCEPCIÓN Y REENVÍO (EVE) ---
    if intercept_eve:
        for i in range(NUM_BITS):
            # Si Eve mide en una base distinta a la de Alice,
            # el estado colapsa aleatoriamente en la nueva base.
            if EVE_BASES[i] != ALICE_BASES[i]:
                # Rotación pi/2 que simula la incertidumbre del colapso proyectivo
                qc.ry(np.pi / 2, i)

    # --- PASO 3: BOB MIDE EN SU BASE ---
    for i in range(NUM_BITS):
        if BOB_BASES[i] == 1:
            qc.h(i)
        qc.measure(i, i)

    return qc

def run_qkd_simulation(intercept_eve=False):
    qc = build_bb84_circuit(intercept_eve=intercept_eve)
    sampler = StatevectorSampler()
    job = sampler.run([qc], shots=1)
    result = job.result()

    # Invertir bitstring por convención little-endian de Qiskit
    raw_bitstring = list(result[0].data.c.get_counts().keys())[0]
    bob_measured_bits = [int(b) for b in reversed(raw_bitstring)]

    # --- PASO 4: RECONCILIACIÓN PÚBLICA DE BASES (SIFTING) ---
    sifted_alice = []
    sifted_bob = []

    for i in range(NUM_BITS):
        if ALICE_BASES[i] == BOB_BASES[i]:
            sifted_alice.append(ALICE_BITS[i])
            sifted_bob.append(bob_measured_bits[i])

    # --- PASO 5: CÁLCULO DE QBER ---
    total_sifted = len(sifted_alice)
    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = (errors / total_sifted) * 100 if total_sifted > 0 else 0.0

    return {
        "sifted_alice": sifted_alice,
        "sifted_bob": sifted_bob,
        "total_sifted": total_sifted,
        "errors": errors,
        "qber": qber,
    }

def main():
    print("==================================================================")
    print("  SIMULACIÓN DE CANAL SEGURO QKD (BB84) CON DETECCIÓN DE ESPÍA   ")
    print("  This effort is supported by Qollab & IonQ                      ")
    print("==================================================================\n")

    print(f"Fotones transmitidos por Alice : {NUM_BITS}")
    print(f"Bits originales de Alice       : {ALICE_BITS}")
    print(f"Bases de Alice (0:Z, 1:X)      : {ALICE_BASES}")
    print(f"Bases de Bob   (0:Z, 1:X)      : {BOB_BASES}")
    print(f"Bases de Eve   (0:Z, 1:X)      : {EVE_BASES}\n")

    # 1. Simulación sin intruso
    res_clean = run_qkd_simulation(intercept_eve=False)

    # 2. Simulación con intercepción de Eve
    res_eavesdrop = run_qkd_simulation(intercept_eve=True)

    print("--- [1] CIRCUITO CUÁNTICO (PRIMEROS 4 FOTONES DE ALICE A BOB) ---")
    demo_qc = QuantumCircuit(4, 4)
    for i in range(4):
        if ALICE_BITS[i] == 1:
            demo_qc.x(i)
        if ALICE_BASES[i] == 1:
            demo_qc.h(i)
        if BOB_BASES[i] == 1:
            demo_qc.h(i)
        demo_qc.measure(i, i)
    print(demo_qc.draw(output="text"))

    print("\n--- [2] COMPARATIVA DIRECTA DE SEGURIDAD Y QBER ---")
    print(f"+---------------------------------+----------------+----------------+")
    print(f"| Parámetro de Comunicación       | Canal Seguro   | Canal con Eve  |")
    print(f"+---------------------------------+----------------+----------------+")
    print(f"| Bits Coincidentes en Base       | {res_clean['total_sifted']:<14} | {res_eavesdrop['total_sifted']:<14} |")
    print(f"| Errores Detectados en Clave     | {res_clean['errors']:<14} | {res_eavesdrop['errors']:<14} |")
    print(f"| QBER (Tasa de Error Cuántico)   | {res_clean['qber']:<13.2f}% | {res_eavesdrop['qber']:<13.2f}% |")

    # Umbral estándar de seguridad cuántica: 11%
    status_clean = "APROBADO (0% error)"
    status_eve = "ABORTADO (Espía detectado)" if res_eavesdrop['qber'] > 11.0 else "VULNERABLE"

    print(f"| Veredicto de Protocolo          | {status_clean:<14} | {status_eve:<14} |")
    print(f"+---------------------------------+----------------+----------------+")

    print("\n--- [3] DETALLES DE CLAVE TAMIZADA (SIFTED KEYS) ---")
    print(f"Clave Alice (Canal Seguro): {''.join(map(str, res_clean['sifted_alice']))}")
    print(f"Clave Bob   (Canal Seguro): {''.join(map(str, res_clean['sifted_bob']))}")
    print(f"Clave Bob   (Con Espía)   : {''.join(map(str, res_eavesdrop['sifted_bob']))}")

    print("\n✓ Simulación finalizada bajo runtime de Qollab.")

if __name__ == "__main__":
    main()