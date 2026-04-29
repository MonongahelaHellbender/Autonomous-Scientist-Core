import numpy as np
from pysr import PySRRegressor

# Historical H0 Data
z = np.array([0.01, 0.05, 0.1, 0.15, 0.25, 0.4, 0.55, 0.7, 1.0, 1.5, 2.0, 2.5, 1100.0])
h0 = np.array([73.04, 72.5, 71.9, 71.5, 71.0, 70.8, 70.5, 70.3, 70.1, 69.8, 69.5, 69.2, 67.4])

model = PySRRegressor(
    niterations=100,
    binary_operators=["+", "-", "*", "/"],
    unary_operators=["log10", "exp"],
    model_selection="best"
)

print("--- ADVERSARIAL TEST: Searching for a simpler truth than 'Drift' ---")
model.fit(z.reshape(-1, 1), h0)
print("\nTop Candidate Equations:")
print(model.equations_)
