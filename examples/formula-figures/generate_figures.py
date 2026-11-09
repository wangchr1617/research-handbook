"""Draw the worked illustrations linked from the research handbook notes."""

from math import erf
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle
import numpy as np

ASSETS = Path(__file__).resolve().parent / "assets"
TEAL = "#08796e"
ORANGE = "#b64c20"
PURPLE = "#6a4b9a"
INK = "#223842"
MUTED = "#566a74"
GRID = "#dce5e8"

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.labelcolor": INK,
    "axes.edgecolor": "#9cb0ba",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "axes.formatter.use_mathtext": True,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "legend.frameon": False,
    "legend.fontsize": 10,
    "lines.linewidth": 2.2,
})


def chart(width=6.4, height=3.6, columns=1):
    return plt.subplots(1, columns, figsize=(width, height), layout="constrained")


def save(fig, name):
    fig.savefig(ASSETS / (name + ".png"), dpi=180, facecolor="white")
    plt.close(fig)


def axis_grid(ax):
    ax.grid(color=GRID, linewidth=0.75)


def periodic_image():
    fig, ax = chart(height=2.5)
    box, a, b = 12, 1.0, 11.5
    image = b - box
    ax.axvspan(0, box, color="#edf6f2", zorder=0)
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.axvline(box, color=MUTED, linewidth=1)
    ax.scatter([a, b], [0, 0], color=TEAL, s=65, zorder=3)
    ax.scatter([image], [0], facecolors="white", edgecolors=TEAL, s=65, zorder=3)
    ax.text(a + 0.12, 0.03, r"$A$", ha="left", va="bottom")
    ax.text(b, 0.06, r"$B$", ha="center")
    ax.text(image - 0.12, 0.03, r"$B-L$", ha="right", va="bottom")
    for start, stop, height, color, label in [
        (a, b, 0.55, MUTED, r"Direct: $10.5$ Å"),
        (image, a, -0.45, ORANGE, r"Minimum image: $1.5$ Å"),
    ]:
        ax.annotate("", (stop, height), (start, height),
                    arrowprops={"arrowstyle": "<->", "color": color, "lw": 1.6})
        ax.text((start + stop) / 2, height + (0.07 if height > 0 else -0.12),
                label, color=color, ha="center")
    ax.set(xlim=(-2.0, 12.8), ylim=(-0.7, 0.9), xticks=[0, 3, 6, 9, 12],
           yticks=[], xlabel=r"Coordinate $x$ (Å)")
    ax.spines["left"].set_visible(False)
    save(fig, "periodic_image")


def neb_interpolation():
    fig, ax = chart(height=3.2)
    start = np.array([-2.0, 0])
    anchor = np.array([-0.4, 1.2])
    end = np.array([2.0, 0])
    images = np.vstack([np.linspace(start, anchor, 4), np.linspace(anchor, end, 4)[1:]])
    ax.add_patch(Circle((0, 0), 0.52, facecolor="#e8e9ed", edgecolor=MUTED))
    ax.text(0, -0.12, "Close\ncontact", ha="center", va="top", fontsize=9, color=MUTED)
    ax.plot([-2, 2], [0, 0], "--", color=ORANGE, label="Endpoint interpolation")
    ax.plot(*images.T, "o-", color=TEAL, label="Piecewise interpolation")
    for i, (x, y) in enumerate(images, 1):
        ax.annotate(str(i), (x, y), xytext=(0, 8), textcoords="offset points", ha="center")
    ax.scatter(*images[[0, 3, 6]].T, s=68, color=TEAL, edgecolors="white", zorder=4)
    ax.set(xlim=(-2.5, 2.5), ylim=(-0.59, 1.63), aspect="equal",
           xlabel=r"$x$ (Å)", ylabel=r"$y$ (Å)")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "neb_interpolation")


def density_profile():
    fig, (profile, cumulative) = plt.subplots(
        2, 1, figsize=(6.4, 4.7), sharex=True, layout="constrained"
    )
    z = np.linspace(-4, 4, 401)
    sigma = 0.48
    moved = 0.25

    def gaussian(center):
        return moved * np.exp(-0.5 * ((z - center) / sigma) ** 2) / (np.sqrt(2 * np.pi) * sigma)

    local = gaussian(1.2) - gaussian(-1.2)
    integral = moved * np.array([
        (erf((value - 1.2) / (np.sqrt(2) * sigma))
         - erf((value + 1.2) / (np.sqrt(2) * sigma))) / 2
        for value in z
    ])
    integral -= integral[0]
    profile.plot(z, local, color=TEAL)
    profile.fill_between(z, 0, local, where=local >= 0, color=TEAL, alpha=0.18, label="Accumulation")
    profile.fill_between(z, 0, local, where=local <= 0, color=ORANGE, alpha=0.21, label="Depletion")
    profile.set(ylabel="Plane integral (e/Å)")
    profile.legend(loc="lower right")
    cumulative.plot(z, integral, color=PURPLE)
    cumulative.set(xlabel=r"Surface-normal coordinate $z$ (Å)", ylabel="Cumulative change (e)")
    for ax in (profile, cumulative):
        ax.axhline(0, color=MUTED, linewidth=0.8)
        axis_grid(ax)
    save(fig, "density_profile")


def interface_temperature():
    fig, ax = chart()
    for edge, stop, intercept, slope, color, label in [
        (-9, -1.5, 305, -0.44, TEAL, "Left fit"),
        (9, 1.5, 300, -0.33, ORANGE, "Right fit"),
    ]:
        x = np.linspace(edge, stop, 8)
        ax.plot(x, intercept + slope * x, "o-", color=color, ms=4.5, label=label)
        ax.plot([stop, 0], [intercept + slope * stop, intercept], "--", color=color, lw=1.6)
        ax.scatter([0], [intercept], color=color, s=35, zorder=4)
    ax.axvspan(-1.5, 1.5, color="#eef1f6", zorder=0)
    ax.axvline(0, color=MUTED, lw=0.9)
    ax.annotate("", (0, 305), (0, 300), arrowprops={"arrowstyle": "<->", "color": PURPLE, "lw": 1.9})
    ax.text(0.42, 302.5, r"$\Delta T_\mathrm{int}=5$ K", va="center", color=PURPLE)
    ax.set(xlabel=r"Position normal to the interface $z$ (nm)", ylabel=r"Temperature $T$ (K)")
    ax.legend(loc="upper right")
    axis_grid(ax)
    save(fig, "interface_temperature")


def finite_difference_error():
    fig, ax = chart()
    h = np.geomspace(0.001, 0.08, 251)
    truncation = 0.01 * (h / 0.01) ** 2
    noise = 0.01 * 0.01 / h
    envelope = truncation + noise
    ax.loglog(h, truncation, color=TEAL, label=r"Truncation $\propto h^2$")
    ax.loglog(h, noise, "--", color=ORANGE, label=r"Force noise $\propto 1/h$")
    ax.loglog(h, envelope, color=PURPLE, label="Sum of the two scales")
    idx = np.argmin(envelope)
    ax.scatter(h[idx], envelope[idx], color=PURPLE, zorder=4, s=35)
    ax.set(xlabel=r"Displacement $h$ (Å)", ylabel="Error scale (a.u.)")
    ax.legend(loc="upper center")
    axis_grid(ax)
    save(fig, "finite_difference_error")


def acsf_radial():
    fig, ax = chart()
    r = np.linspace(0, 4.6, 501)
    cutoff_radius = 4
    cutoff = np.where(r < cutoff_radius, (1 + np.cos(np.pi * r / cutoff_radius)) / 2, 0)
    ax.plot(r, cutoff, ":", color=MUTED, label=r"Cutoff $f_c$")
    for center, eta, color, line in [(1, 1.2, TEAL, "-"), (2.3, 1.2, ORANGE, "--"),
                                    (2.3, 5.0, PURPLE, "-.")]:
        ax.plot(r, np.exp(-eta * (r - center) ** 2) * cutoff, line, color=color,
                label=rf"$R_s={center:g}$ Å, $\eta={eta:g}$ Å$^{{-2}}$")
    ax.axvline(cutoff_radius, color=MUTED, linewidth=1)
    ax.text(cutoff_radius, 0.12, r"$r_c$", ha="right", color=MUTED)
    ax.set(xlabel=r"Neighbor distance $r_{ij}$ (Å)", ylabel="Single-neighbor contribution",
           ylim=(-0.02, 1.05))
    ax.legend(loc="upper right")
    axis_grid(ax)
    save(fig, "acsf_radial")


def relaxed_hessian():
    fig, (contours, sections) = chart(width=8.0, height=3.7, columns=2)
    axis = np.linspace(-1.6, 1.6, 161)
    x, y = np.meshgrid(axis, axis)
    energy = x ** 2 + x * y + y ** 2
    contours.contour(x, y, energy, levels=[0.25, 0.75, 1.5, 2.5, 3.5],
                     colors=["#a5b9c0"], linewidths=1)
    contours.plot(axis, np.zeros_like(axis), "--", color=ORANGE)
    contours.plot(axis, -axis / 2, color=TEAL)
    contours.set(xlabel=r"Displacement $x$ (a.u.)", ylabel=r"Displacement $y$ (a.u.)",
                 aspect="equal", title="Paths on the energy surface")
    sections.plot(axis, axis ** 2, "--", color=ORANGE, label=r"Fixed $y=0$: $k=2$")
    sections.plot(axis, 0.75 * axis ** 2, color=TEAL, label=r"Relaxed $y=-x/2$: $k=1.5$")
    sections.set(xlabel=r"Displacement $x$ (a.u.)", ylabel=r"Energy $E$ (a.u.)", title="Energy along each path")
    sections.legend(loc="upper center", fontsize=9)
    axis_grid(sections)
    save(fig, "relaxed_hessian")


def cbs_extrapolation():
    fig, axes = chart(width=8.0, height=3.35, columns=2)
    for ax, transform, coefficient, limit, title, label, color in [
        (axes[0], lambda x: np.exp(-1.6 * np.sqrt(x)), 34, -7, "SCF contribution",
         r"$e^{-\alpha\sqrt{X}}$  ($\alpha=1.6$)", TEAL),
        (axes[1], lambda x: x ** -3.0, 120, -13, "Correlation contribution",
         r"$X^{-\beta}$  ($\beta=3$)", ORANGE),
    ]:
        x = transform(np.array([3.0, 4.0]))
        ax.plot([0, x[1]], [limit, limit + coefficient * x[1]], "--", color=color)
        ax.plot(x, limit + coefficient * x, "o-", color=color, ms=6)
        ax.scatter(0, limit, marker="D", color=PURPLE, zorder=4, s=36)
        ax.annotate("CBS", (0, limit), xytext=(10, 3), textcoords="offset points")
        for n, value in zip((3, 4), x):
            ax.annotate(f"X = {n}", (value, limit + coefficient * value),
                        xytext=(-8, 9), textcoords="offset points", ha="right")
        ax.set(xlabel=label, ylabel="Model energy (a.u.)", title=title,
               xlim=(-x[0] * 0.08, x[0] * 1.12))
        ax.margins(y=0.19)
        axis_grid(ax)
    save(fig, "cbs_extrapolation")


def counterpoise():
    fig, ax = chart(height=3.6)
    ab, isolated, ghosts = -10, 0, -3
    ax.hlines([ab, isolated, ghosts], [0.0, 0.08, 0.56], [1.0, 0.42, 0.91],
              colors=[INK, ORANGE, TEAL], linewidths=2)
    ax.text(0.08, isolated + 0.3, r"$E_A^A+E_B^B$", color=ORANGE)
    ax.text(0.56, ghosts + 0.3, r"$E_A^{AB}+E_B^{AB}$", color=TEAL)
    ax.text(0.5, ab - 0.56, r"$E_{AB}^{AB}$", ha="center")
    for xpos, ref, color, label in [(0.25, isolated, ORANGE, r"Raw: $-10$"),
                                    (0.73, ghosts, TEAL, r"CP: $-7$")]:
        ax.annotate("", (xpos, ab), (xpos, ref), arrowprops={"arrowstyle": "->", "color": color, "lw": 1.8})
        ax.text(xpos + 0.04, (ref + ab) / 2, label, color=color, va="center")
    ax.set(xlim=(-0.02, 1.05), ylim=(-11.1, 1), xticks=[],
           yticks=[-10, -3, 0], ylabel="Relative energy (a.u.)")
    ax.spines["bottom"].set_visible(False)
    save(fig, "counterpoise")


def altbc_pair():
    fig, (geometry, counts) = chart(width=8.2, height=3.5, columns=2)
    short, long = 2.7, 3.5
    theta = 170
    endpoint = np.array([np.cos(np.deg2rad(180 - theta)), np.sin(np.deg2rad(180 - theta))]) * long
    geometry.plot([-short, 0, endpoint[0]], [0, 0, endpoint[1]], color=MUTED, linewidth=1.5)
    geometry.scatter([-short, 0, endpoint[0]], [0, 0, endpoint[1]], c=[TEAL, INK, ORANGE], s=68, zorder=3)
    geometry.add_patch(Arc((0, 0), 2.6, 2.6, theta1=180 - theta, theta2=180, color=PURPLE, lw=1.5))
    geometry.text(0, 1.48, r"$170^\circ$", ha="center", color=PURPLE)
    for name, x, y in [("A", -short, 0), ("B", 0, 0), ("C", *endpoint)]:
        geometry.annotate(name, (x, y), xytext=(0, -17), textcoords="offset points", ha="center")
    geometry.text(-1.7, -0.52, r"$r_1=2.7$ Å", ha="center", color=TEAL)
    geometry.text(2.0, -0.52, r"$r_2=3.5$ Å", ha="center", color=ORANGE)
    geometry.set(xlim=(-3.1, 3.95), ylim=(-0.8, 2.25), aspect="equal",
                 title="One accepted neighbor pair")
    geometry.axis("off")
    counts.plot([2.4, 3.8], [2.4, 3.8], "--", color=MUTED, lw=1)
    counts.scatter([short, long], [long, short], marker="s", c=[TEAL, ORANGE], s=72, zorder=4)
    for x, y in [(short, long), (long, short)]:
        counts.annotate("+1", (x, y), xytext=(10, 4), textcoords="offset points")
    counts.set(xlim=(2.4, 3.8), ylim=(2.4, 3.8), xticks=[short, long], yticks=[short, long],
               xlabel=r"$r_1$ (Å)", ylabel=r"$r_2$ (Å)", aspect="equal", title="Two ordered contributions")
    axis_grid(counts)
    save(fig, "altbc_pair")


def binary_hull():
    fig, ax = chart()
    x = np.array([0, 0.25, 0.65, 1])
    energies = np.array([0, -0.44, -0.60, 0])
    composition, candidate = 0.45, -0.36
    reference = np.interp(composition, x, energies)
    ax.plot(x, energies, "o-", color=TEAL, label="Reference convex hull")
    ax.scatter(composition, candidate, color=ORANGE, marker="D", s=47, label="Candidate")
    ax.scatter(composition, reference, facecolors="white", edgecolors=TEAL, zorder=5, s=42)
    ax.annotate("", (composition, candidate), (composition, reference),
                arrowprops={"arrowstyle": "<->", "color": PURPLE, "lw": 1.7})
    ax.text(composition + 0.045, (candidate + reference) / 2,
            rf"$\Delta e={candidate - reference:.2f}$ eV/atom", va="center", color=PURPLE)
    ax.set(xlabel="B atomic fraction", ylabel="Formation energy (eV/atom)", ylim=(-0.7, 0.08))
    ax.legend(loc="upper center")
    axis_grid(ax)
    save(fig, "binary_hull")


def graphite_capacity():
    fig, ax = chart()
    x = np.linspace(0, 1, 201)
    faraday = 96485.33212
    host_mass = 6 * 12.011
    lithiated_mass = host_mass + x * 6.94
    charge = x * faraday / 3.6
    for capacity, color, line, label in [
        (charge / host_mass, TEAL, "-", r"Host mass $6M_\mathrm{C}$"),
        (charge / lithiated_mass, ORANGE, "--", r"Lithiated mass $6M_\mathrm{C}+xM_\mathrm{Li}$"),
    ]:
        ax.plot(x, capacity, line, color=color, label=label)
        ax.scatter(1, capacity[-1], s=36, color=color, zorder=4)
        ax.annotate(f"{capacity[-1]:.0f}", (1, capacity[-1]),
                    xytext=(8, 0), textcoords="offset points", va="center", color=color)
    ax.set(xlabel=r"Lithium content $x$ in Li$_x$C$_6$", ylabel="Specific capacity (mAh/g)",
           xlim=(0, 1.11), ylim=(0, 410))
    ax.legend(loc="upper left")
    axis_grid(ax)
    save(fig, "graphite_capacity")


def unit_vector_geometry():
    fig, ax = chart(width=5.1, height=3.45)
    query = np.array([1, 0])
    document = np.array([0.5, np.sqrt(3) / 2])
    ax.add_patch(Circle((0, 0), 1, fill=False, linestyle=":", color=MUTED, linewidth=1))
    for vector, color in [(query, TEAL), (document, ORANGE)]:
        ax.annotate("", vector, (0, 0), arrowprops={"arrowstyle": "->", "color": color, "lw": 2.2})
    ax.plot([query[0], document[0]], [query[1], document[1]], "--", color=PURPLE, linewidth=1.6)
    ax.add_patch(Arc((0, 0), 0.59, 0.59, theta1=0, theta2=60, color=MUTED, lw=1.4))
    ax.text(0.32, 0.14, r"$60^\circ$")
    ax.text(1.08, -0.025, r"$q$", color=TEAL)
    ax.text(0.49, 0.92, r"$x$", color=ORANGE)
    ax.text(0.83, 0.46, r"$\|q-x\|=1$", color=PURPLE)
    ax.set(xlim=(-0.24, 1.47), ylim=(-0.22, 1.13), aspect="equal", title="Unit-vector similarity")
    ax.axis("off")
    save(fig, "unit_vector_geometry")


def neb_force_projection():
    fig, axes = chart(width=8.2, height=2.8, columns=3)
    for ax, title, tangent_force in zip(
        axes, ["Physical force", "Ordinary NEB", "Climbing image"], [1.0, 0.0, -1.0]
    ):
        ax.axhline(0, color=MUTED, linestyle=":", linewidth=1)
        ax.annotate(r"$\hat{\tau}$", (1.05, 0), (0.75, 0),
                    arrowprops={"arrowstyle": "->", "color": MUTED}, color=MUTED)
        ax.annotate("", (0, 0.72), (0, 0), arrowprops={"arrowstyle": "->", "color": TEAL, "lw": 2})
        if tangent_force:
            ax.annotate("", (tangent_force, 0), (0, 0),
                        arrowprops={"arrowstyle": "->", "color": ORANGE, "lw": 2})
        ax.annotate("", (tangent_force, 0.72), (0, 0),
                    arrowprops={"arrowstyle": "->", "color": INK, "lw": 2})
        ax.set(xlim=(-1.25, 1.25), ylim=(-0.24, 1.0), aspect="equal", title=title)
        ax.set_axis_off()
    save(fig, "neb_force_projection")


def rotated_vector():
    fig, ax = chart(width=5.1, height=3.5)
    ax.add_patch(Circle((0, 0), 1, fill=False, linestyle=":", edgecolor=MUTED))
    for vector, color, label in [((1, 0), TEAL, r"$v=(1,0)$"), ((0, 1), ORANGE, r"$Qv=(0,1)$")]:
        ax.annotate("", vector, (0, 0), arrowprops={"arrowstyle": "->", "lw": 2.6, "color": color})
        ax.annotate(label, vector, xytext=(6, 6), textcoords="offset points", color=color)
    ax.add_patch(Arc((0, 0), 0.64, 0.64, theta1=0, theta2=90, color=PURPLE))
    ax.text(0.28, 0.28, r"$90^\circ$", color=PURPLE)
    ax.text(-0.9, -0.64, r"$\|v\|=\|Qv\|=1$", color=MUTED)
    ax.set(xlim=(-1.12, 1.65), ylim=(-1.1, 1.2), aspect="equal", xlabel=r"$x$", ylabel=r"$y$")
    axis_grid(ax)
    save(fig, "rotated_vector")


def gaussian_exponents():
    fig, ax = chart()
    radius = np.linspace(0, 5, 251)
    for exponent, color, line in [(2, ORANGE, "--"), (0.6, PURPLE, "-."), (0.15, TEAL, "-")]:
        ax.plot(radius, np.exp(-exponent * radius ** 2), line, color=color,
                label=rf"$\alpha={exponent:g}$ bohr$^{{-2}}$")
    ax.set(xlabel=r"Distance $r$ (bohr)", ylabel=r"Relative amplitude $\chi(r)/\chi(0)$")
    ax.legend()
    axis_grid(ax)
    save(fig, "gaussian_exponents")


def ring_probe():
    fig, ax = chart(width=6.5, height=4.3)
    for center in [(-3, 0), (3, 0)]:
        ax.add_patch(Circle(center, 1.7, facecolor="#edf0f2", edgecolor=MUTED))
    for height, color, label in [(0, TEAL, "In plane: 1.30 Å"), (2, ORANGE, "Above plane: 1.91 Å")]:
        radius = np.hypot(3, height) - 1.7
        ax.add_patch(Circle((0, height), radius, fill=False, edgecolor=color,
                            linestyle="-" if height else "--", linewidth=2))
        ax.plot(0, height, ".", color=color, label=label)
    ax.axhline(0, color=MUTED, linestyle=":", linewidth=1)
    ax.set(xlim=(-5, 5), ylim=(-1.9, 4.3), aspect="equal",
           xlabel="In-plane coordinate (Å)", ylabel="Height above ring (Å)")
    ax.legend(loc="upper left")
    save(fig, "ring_probe")


def bcp_curvature():
    fig, axes = chart(width=8.1, height=2.9, columns=3)
    coordinate = np.linspace(-1, 1, 161)
    for ax, name, eigenvalue in zip(axes, ["Transverse 1", "Transverse 2", "Along bond path"], [-2, -1, 4]):
        ax.plot(coordinate, eigenvalue * coordinate ** 2 / 2, color=TEAL if eigenvalue < 0 else ORANGE)
        ax.scatter([0], [0], color=PURPLE, zorder=3)
        ax.set(title=rf"{name}: $\lambda={eigenvalue}$", ylim=(-1.2, 2.2),
               xlabel="Local displacement (a.u.)")
        axis_grid(ax)
    axes[0].set_ylabel(r"Density change $\Delta\rho$ (a.u.)")
    save(fig, "bcp_curvature")


def soap_density_slice():
    fig, axes = chart(width=8.2, height=3.5, columns=2)
    coordinate = np.linspace(-2.4, 2.4, 201)
    x, y = np.meshgrid(coordinate, coordinate)
    neighbors = np.array([[-0.8, 0.3], [0.15, 1.1], [0.95, -0.5]])
    for ax, sigma in zip(axes, [0.2, 0.55]):
        density = sum(np.exp(-((x-a)**2+(y-b)**2)/(2*sigma**2)) for a, b in neighbors)
        mesh = ax.pcolormesh(x, y, density, cmap="cividis", vmin=0, vmax=1.2, shading="auto")
        ax.scatter(*neighbors.T, s=19, facecolors="none", edgecolors="white")
        ax.set(aspect="equal", title=rf"$\sigma={sigma}$ Å", xlabel=r"$x$ (Å)")
    axes[0].set_ylabel(r"$y$ (Å)")
    fig.colorbar(mesh, ax=axes, label="Model density (a.u.)")
    save(fig, "soap_density_slice")


def matrix_error_projection():
    fig, ax = chart()
    state = np.linspace(0, 90, 181)
    angle = np.deg2rad(state)
    ax.plot(state, 0.04*np.cos(angle)**2, color=TEAL,
            label=r"$\delta H=\mathrm{diag}(0.04,0)$ eV")
    ax.plot(state, 0.04*np.sin(angle)**2, "--", color=ORANGE,
            label=r"$\delta H=\mathrm{diag}(0,0.04)$ eV")
    ax.set(xlabel=r"Reference state angle $\theta$ (degrees)", ylabel=r"First-order shift $\delta\epsilon$ (eV)",
           xticks=[0, 30, 60, 90], ylim=(-0.002, 0.048))
    ax.legend(loc="upper center")
    axis_grid(ax)
    save(fig, "matrix_error_projection")


def solvation_cycle():
    fig, ax = chart(height=3.1)
    for x, y, label in [(0, 1, "Gas\n1 atm"), (1, 1, "Gas\n1 mol/L"),
                        (1, 0, "Solution\n1 mol/L")]:
        ax.scatter(x, y, color=TEAL, zorder=3)
        ax.text(x, y + (0.10 if y else -0.12), label, ha="center", va="bottom" if y else "top")
    for start, stop, label, position, align in [
        ((0, 1), (1, 1), r"$\Delta G_{\rm std}$", (0.5, 1.07), "center"),
        ((1, 1), (1, 0), r"$\Delta G_{\rm solv}^{c\to c}$", (1.08, 0.52), "left"),
    ]:
        ax.annotate("", stop, start, arrowprops={"arrowstyle": "->", "color": PURPLE, "lw": 2})
        ax.text(*position, label, ha=align, color=PURPLE)
    ax.set(xlim=(-0.27, 1.55), ylim=(-0.43, 1.48))
    ax.set_axis_off()
    save(fig, "solvation_cycle")


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    periodic_image()
    neb_interpolation()
    density_profile()
    interface_temperature()
    finite_difference_error()
    acsf_radial()
    relaxed_hessian()
    cbs_extrapolation()
    counterpoise()
    altbc_pair()
    binary_hull()
    graphite_capacity()
    unit_vector_geometry()
    neb_force_projection()
    rotated_vector()
    gaussian_exponents()
    ring_probe()
    bcp_curvature()
    soap_density_slice()
    matrix_error_projection()
    solvation_cycle()
