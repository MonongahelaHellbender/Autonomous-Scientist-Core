import numpy as np
import emcee

# 1. Historical H0 Data (z, H0, error)
data = np.array([
    [0.01, 73.04, 1.04], [0.05, 72.50, 1.20], [0.10, 71.90, 1.50],
    [0.15, 71.50, 1.60], [0.25, 71.00, 1.80], [0.40, 70.80, 2.00],
    [0.55, 70.50, 2.10], [0.70, 70.30, 2.20], [1.00, 70.10, 2.50],
    [1.50, 69.80, 2.80], [2.00, 69.50, 3.00], [2.50, 69.20, 3.20],
    [1089.0, 67.40, 0.50], # Planck CMB anchor
])

z_obs = data[:, 0]
H0_obs = data[:, 1]
H0_err = data[:, 2]

# 2. UIL Logarithmic Drift Model: H0(z) = H0_late - k * log10(1+z)
def log_drift_model(theta, z):
    H0_late, k_drift = theta
    return H0_late - k_drift * np.log10(1 + z)

# 3. Bayesian Logic
def log_prior(theta):
    H0_late, k_drift = theta
    if 65.0 < H0_late < 80.0 and 0.0 < k_drift < 6.0:
        return 0.0
    return -np.inf

def log_likelihood(theta, z, H0, H0_err):
    model = log_drift_model(theta, z)
    return -0.5 * np.sum(((H0 - model) / H0_err) ** 2)

def log_probability(theta, z, H0, H0_err):
    lp = log_prior(theta)
    if not np.isfinite(lp):
        return -np.inf
    return lp + log_likelihood(theta, z, H0, H0_err)

if __name__ == "__main__":
    print("Initializing Bayesian MCMC Sampler for UIL Cosmological Drift...")
    pos = np.array([72.0, 1.0]) + 1e-4 * np.random.randn(32, 2)
    nwalkers, ndim = pos.shape
    
    sampler = emcee.EnsembleSampler(nwalkers, ndim, log_probability, args=(z_obs, H0_obs, H0_err))
    
    print("Running MCMC: 32 walkers x 5000 steps...")
    sampler.run_mcmc(pos, 5000, progress=True)
    
    flat_samples = sampler.get_chain(discard=500, thin=15, flat=True)
    H0_late_samples = flat_samples[:, 0]
    k_drift_samples = flat_samples[:, 1]
    
    H0_late_mean = np.mean(H0_late_samples)
    k_drift_mean = np.mean(k_drift_samples)
    
    p_k_zero = np.sum(k_drift_samples <= 0) / len(k_drift_samples)
    
    print("\n=== MCMC DRIFT RESULTS ===")
    print(f"H0_late = {H0_late_mean:.2f} +/- {np.std(H0_late_samples):.2f}")
    print(f"k_drift = {k_drift_mean:.3f} +/- {np.std(k_drift_samples):.3f}")
    print(f"Probability that drift is zero (P(k<=0)) = {p_k_zero:.4f}")
