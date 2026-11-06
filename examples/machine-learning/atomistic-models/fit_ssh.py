"""从能谱拟合 SSH 模型并展示规范歧义；用法：python fit_ssh.py。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares


def matrices(k, parameters):
    onsite, t1, t2 = parameters
    result = np.zeros((len(k), 2, 2), dtype=complex)
    result[:, 0, 0] = result[:, 1, 1] = onsite
    result[:, 0, 1] = t1 + t2 * np.exp(-1j*k)
    result[:, 1, 0] = result[:, 0, 1].conj()
    return result


def main():
    config = json.loads(Path(__file__).with_name("ssh.json").read_text())
    reference_parameters = [config[key] for key in ["onsite_eV", "t1_eV", "t2_eV"]]
    train_k = np.linspace(-np.pi, np.pi, config["train_kpoints"], endpoint=False)
    labels = np.linalg.eigvalsh(matrices(train_k, reference_parameters))
    def residual(parameters):
        return (np.linalg.eigvalsh(matrices(train_k, parameters))-labels).ravel()
    fit = least_squares(residual, config["initial_parameters_eV"], xtol=1e-12, gtol=1e-12, ftol=1e-12)
    test_k = np.linspace(-np.pi, np.pi, config["test_kpoints"])
    reference = np.linalg.eigvalsh(matrices(test_k, reference_parameters))
    prediction = np.linalg.eigvalsh(matrices(test_k, fit.x))
    rmse = float(np.sqrt(np.mean((prediction-reference)**2)))
    assert fit.success and rmse < 1e-8
    # U=diag(1,-1) 翻转所有非对角跃迁，能谱保持不变。
    flipped = [fit.x[0], -fit.x[1], -fit.x[2]]
    assert np.allclose(np.linalg.eigvalsh(matrices(test_k, flipped)), prediction)
    gap = float(2*abs(abs(fit.x[1])-abs(fit.x[2])))
    assert abs(gap - 0.6) < 1e-8
    Path("results").mkdir(exist_ok=True)
    np.savetxt("results/ssh_bands.csv", np.column_stack([test_k, reference, prediction]),
               delimiter=",", header="ka,ref_lower_eV,ref_upper_eV,fit_lower_eV,fit_upper_eV", comments="")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(test_k/np.pi, reference, color="black", lw=2)
    ax.plot(test_k[::12]/np.pi, prediction[::12], "o", color="#0072B2", ms=4)
    ax.set(xlabel=r"$ka/\pi$", ylabel="Energy (eV)", title="SSH model: analytic labels and spectral fit")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig("results/ssh_bands.png", dpi=180)
    plt.close(fig)
    report = {"label_source": config["label_source"], "fit_parameters_eV": fit.x.tolist(),
              "test_rmse_eV": rmse, "gap_eV": gap,
              "sign_flipped_parameters_eV": flipped}
    Path("results/ssh_fit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
