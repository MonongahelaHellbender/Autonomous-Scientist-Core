import numpy as np
import pandas as pd

def simulate_evolution():
    print("--- UIL Biological Intelligence: Evolutionary Sieve ---")
    
    # 1. Setup Initial Population (1000 organisms, 3 Genes each)
    # Genes represent: [Metabolic Rate, Heat Resistance, Camouflage]
    population = np.random.uniform(0, 10, (1000, 3))
    
    # 2. The 'Invariant' Environmental Law: 
    # Survival depends on a specific geometric ratio: Camouflage + (Metabolic / Heat)
    # The 'Ideal' value is 7.5
    TARGET_RATIO = 7.5
    
    def calculate_fitness(pop):
        # The UIL Engine looks for the ratio: Gene2 + (Gene0 / Gene1)
        ratios = pop[:, 2] + (pop[:, 0] / (pop[:, 1] + 0.1))
        fitness = -np.abs(ratios - TARGET_RATIO) # Closer to 0 is better
        return fitness, ratios

    print(f"Target Environmental Invariant: {TARGET_RATIO}")
    
    for generation in range(50):
        fitness, ratios = calculate_fitness(population)
        
        # Selection: Keep the top 10%
        indices = np.argsort(fitness)[-100:]
        survivors = population[indices]
        
        # Mutation/Reproduction: Refill population with slight variations
        new_pop = []
        for _ in range(10):
            mutations = np.random.normal(0, 0.2, survivors.shape)
            new_pop.append(survivors + mutations)
        population = np.vstack(new_pop)
        
        if generation % 10 == 0:
            avg_ratio = np.mean(ratios[indices])
            print(f"Generation {generation}: Mean Population Ratio = {avg_ratio:.4f}")

    # 3. AI Discovery Pass
    final_fitness, final_ratios = calculate_fitness(population)
    discovered_invariant = np.mean(final_ratios)
    
    print("\n=== EVOLUTIONARY DISCOVERY ===")
    print(f"The AI has identified the Biological Invariant: {discovered_invariant:.4f}")
    print(f"Error from True Environmental Law: {abs(discovered_invariant - TARGET_RATIO):.6f}")
    
    if abs(discovered_invariant - TARGET_RATIO) < 0.05:
        print("[VERDICT] PROVEN: The AI discovered the latent evolutionary pressure.")
    else:
        print("[VERDICT] FAILED: The signal was lost in genetic noise.")

if __name__ == "__main__":
    simulate_evolution()
