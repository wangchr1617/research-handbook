"use strict";

const chartColors = ["var(--plot-1)", "var(--plot-2)", "var(--plot-3)"];
const displayNumber = (value, digits = 2) => Number(value.toFixed(digits)).toString();
const labRange = (min, max, count = 241) =>
  Array.from({ length: count }, (_, index) => min + (max - min) * index / (count - 1));
const curve = (xs, evaluate, label, color = 0, dash) => ({
  points: xs.map(x => [x, evaluate(x)]), label, color: chartColors[color], dash,
});
const marker = (x, y, color = 2) => ({ x, y, color: chartColors[color] });
const segment = (x, y0, y1, color = 2, arrow = false) => ({
  points: [[x, y0], [x, y1]], color: chartColors[color], arrow, dash: arrow ? "" : "4 4",
});

const experiments = [
  {
    id: "tight-binding",
    topic: "固体物理 · 01",
    title: "二聚化怎样打开带隙？",
    short: "紧束缚带隙",
    note: "固体物理基础/能带结构与紧束缚模型.md",
    formula: "E<sub>±</sub>(k) = ±√[t₁² + t₂² + 2t₁t₂ cos(ka)]　·　E<sub>g</sub> = 2|t₁ − t₂|",
    prompt: "先预测 t₂ 接近 t₁ 时，两条能带会在哪个 k 点相遇。再切断胞间跃迁，看看能带还随 k 变化吗？",
    detail: "t₁ 和 t₂ 分别为胞内、胞间跃迁。模型取非负跃迁、零在位能，a 为双原子晶胞的长度。横轴用 ka/π 标记第一布里渊区。",
    sliders: [
      ["t1", "胞内跃迁 t₁", 0, 1.5, 0.05, 1, "eV"],
      ["t2", "胞间跃迁 t₂", 0, 1.5, 0.05, 0.6, "eV"],
    ],
    presets: [["等跃迁", { t1: 1, t2: 1 }], ["孤立二聚体", { t1: 1, t2: 0 }]],
    compute({ t1, t2 }) {
      const xs = labRange(-1, 1);
      const energy = x => Math.hypot(t1 + t2 * Math.cos(Math.PI * x), t2 * Math.sin(Math.PI * x));
      const edge = Math.abs(t1 - t2);
      return {
        x: [-1, 1, "ka/π"], y: [-3.2, 3.2, "能量 E（eV）"],
        lines: [curve(xs, energy, "上能带"), curve(xs, x => -energy(x), "下能带", 1, "6 3"),
          segment(1, -edge, edge)],
        dots: [marker(1, edge), marker(1, -edge)],
        readings: [["区边界带隙", `${displayNumber(2 * edge)} eV`],
          ["上下带总能量跨度", `${displayNumber(2 * (t1 + t2))} eV`]],
      };
    },
  },
  {
    id: "phonon",
    topic: "固体物理 · 02",
    title: "质量差怎样改变声子色散？",
    short: "双原子链声子",
    note: "固体物理基础/晶格振动与声子谱.md",
    formula: "ω² = K[1/m₁ + 1/m₂ ± √((1/m₁ + 1/m₂)² − 4 sin²(qa/2)/(m₁m₂))]",
    prompt: "把两种质量调成相等，观察区边界的两支。再将 K 加倍，比较各处频率的变化倍数。",
    detail: "固定 m₁ = 1。a 是双原子晶胞的长度，K 是最近邻弹簧常数，频率采用与笔记算例一致的模型单位。",
    sliders: [
      ["m2", "第二种质量 m₂", 0.5, 4, 0.1, 2, ""],
      ["spring", "弹簧常数 K", 0.5, 2, 0.1, 1, ""],
    ],
    presets: [["等质量", { m2: 1 }], ["K = 2", { spring: 2 }]],
    compute({ m2, spring }) {
      const xs = labRange(-1, 1);
      const sum = 1 + 1 / m2;
      const split = x => Math.hypot(1 - 1 / m2, 2 * Math.cos(Math.PI * x / 2) / Math.sqrt(m2));
      const optical = x => Math.sqrt(spring * (sum + split(x)));
      // Rationalize the smaller eigenvalue so the acoustic branch is zero at Γ.
      const acoustic = x => Math.sqrt(4 * spring / (m2 * (sum + split(x))))
        * Math.abs(Math.sin(Math.PI * x / 2));
      const gap = optical(1) - acoustic(1);
      return {
        x: [-1, 1, "qa/π"], y: [0, 3.6, "角频率 ω（模型单位）"],
        lines: [curve(xs, acoustic, "声学支"), curve(xs, optical, "光学支", 1, "6 3"),
          segment(1, acoustic(1), optical(1))],
        dots: [marker(0, 0), marker(1, acoustic(1)), marker(1, optical(1))],
        readings: [["区边界频率间隔", displayNumber(gap, 3)],
          ["Γ 点光学频率", displayNumber(optical(0), 3)]],
      };
    },
  },
  {
    id: "landau",
    topic: "固体物理 · 03",
    title: "极化双势阱如何合并？",
    short: "铁电双势阱",
    note: "固体物理基础/铁电性与软模.md",
    formula: "F(P) = ½ αP² + ¼ βP⁴　·　α = T/T<sub>c</sub> − 1　·　β = 1",
    prompt: "从低温慢慢升到临界温度。观察两个极小点怎样合并，以及 P = 0 附近的曲线怎样变平。",
    detail: "零电场下的四阶 Landau 模型。温度以临界温度归一化，极化和自由能用模型单位表示。",
    sliders: [["temperature", "相对温度 T/Tc", 0.3, 1.5, 0.01, 0.6, ""]],
    presets: [["临界温度", { temperature: 1 }], ["顺电相", { temperature: 1.2 }]],
    compute({ temperature }) {
      const alpha = temperature - 1;
      const minimum = Math.sqrt(Math.max(0, -alpha));
      const freeEnergy = p => alpha * p ** 2 / 2 + p ** 4 / 4;
      const locations = minimum ? [-minimum, minimum] : [0];
      return {
        x: [-1.4, 1.4, "极化 P（模型单位）"], y: [-0.16, 1.5, "自由能 F（模型单位）"],
        lines: [curve(labRange(-1.4, 1.4), freeEnergy, "自由能")],
        dots: locations.map(p => marker(p, freeEnergy(p))),
        readings: [["极小点 P", minimum ? `±${displayNumber(minimum, 3)}` : "0"],
          ["极小点曲率 F″", displayNumber(alpha + 3 * minimum ** 2, 3)],
          ["零极化点比谷底高", displayNumber(-freeEnergy(minimum), 4)]],
      };
    },
  },
  {
    id: "defect-optical",
    topic: "固体物理 · 04",
    title: "吸收和发射的能量差从哪来？",
    short: "缺陷光学跃迁",
    note: "固体物理基础/点缺陷与光学跃迁.md",
    formula: "E<sub>吸</sub> = E₀ + Sℏω　·　E<sub>发</sub> = E₀ − Sℏω　·　Q₀ = √(2Sℏω/k)",
    prompt: "把 S 调到零，检查两条竖直跃迁的能量是否一样。增大 S 后，比较谷底间距和 Stokes 位移。",
    detail: "等曲率位形坐标模型，固定 E₀ = 2.5 eV、ℏω = 0.05 eV、k = 1 eV/Å²。箭头分别从基态和激发态的谷底起始。S = 0 时两个箭头重合。",
    sliders: [["coupling", "Huang–Rhys 因子 S", 0, 10, 0.25, 3, ""]],
    presets: [["零位移", { coupling: 0 }], ["强耦合示例", { coupling: 10 }]],
    compute({ coupling }) {
      const xs = labRange(-0.65, 1.65);
      const relaxation = coupling * 0.05;
      const q0 = Math.sqrt(2 * relaxation);
      const ground = q => q ** 2 / 2;
      const excited = q => 2.5 + (q - q0) ** 2 / 2;
      return {
        x: [-0.65, 1.65, "位形坐标 Q（Å）"], y: [0, 4, "势能（eV）"],
        lines: [curve(xs, ground, "基态"), curve(xs, excited, "激发态", 1, "6 3"),
          segment(0, 0, excited(0), 0, true), segment(q0, excited(q0), ground(q0), 1, true)],
        dots: [marker(0, 0, 0), marker(q0, 2.5, 1)],
        readings: [["吸收能量 ↑", `${displayNumber(excited(0), 3)} eV`],
          ["发射能量 ↓", `${displayNumber(2.5 - ground(q0), 3)} eV`],
          ["Stokes 位移", `${displayNumber(2 * relaxation, 3)} eV`]],
      };
    },
  },
  {
    id: "dos",
    topic: "电子结构分析 · 05",
    title: "DOS 的峰变矮了，态数去哪了？",
    short: "DOS 展宽",
    note: "计算化学/DOS的展宽、分区与空间分布.md",
    formula: "D(E) = Σᵢ exp[−(E − εᵢ)²/(2σ²)]/(σ√(2π))　·　FWHM = 2√(2 ln 2) σ",
    prompt: "增大 σ，观察两个近邻峰怎样合并。比较图内积分和全能量积分，找出两者差异的来源。",
    detail: "四个示意能级各计一个态。短竖线标出原始能级。曲线的尾部可以延伸到绘图窗口以外。",
    sliders: [["sigma", "Gaussian 标准差 σ", 0.04, 0.65, 0.01, 0.14, "eV"]],
    presets: [["分开近邻峰", { sigma: 0.06 }], ["宽核尾部", { sigma: 0.6 }]],
    compute({ sigma }) {
      const levels = [-1.4, -1.1, 0.7, 1.2];
      const xs = labRange(-2, 2, 401);
      const density = e => levels.reduce((sum, level) =>
        sum + Math.exp(-0.5 * ((e - level) / sigma) ** 2) / (sigma * Math.sqrt(2 * Math.PI)), 0);
      const dos = curve(xs, density, "Gaussian 展宽 DOS");
      const area = dos.points.reduce((sum, [x, y], index, points) =>
        index ? sum + (x - points[index - 1][0]) * (y + points[index - 1][1]) / 2 : sum, 0);
      return {
        x: [-2, 2, "能量 E（eV）"], y: [0, 11, "态密度（states/eV）"],
        lines: [dos, ...levels.map(level => segment(level, 0, 0.9))],
        readings: [["半高全宽", `${displayNumber(2 * Math.sqrt(2 * Math.log(2)) * sigma, 3)} eV`],
          ["图内积分 −2 至 2 eV", `${area.toFixed(3)} 个态`], ["全能量积分", "4 个态"]],
      };
    },
  },
  {
    id: "msd",
    topic: "分子动力学 · 06",
    title: "从哪一段 MSD 拟合扩散系数？",
    short: "MSD 拟合窗口",
    note: "LAMMPS/扩散与输运/LAMMPS均方位移与扩散系数.md",
    formula: "MSD(t) = 6D∞[t − τ(1 − exp(−t/τ))]　·　D<sub>拟合</sub> = 斜率/6",
    prompt: "保持窗口宽度相同，把起点从弹道区移到较晚时刻。比较拟合优度与 D 的误差是否同步改善。",
    detail: "三维各向同性的示意曲线，τ = 5 ps，长时 D∞ = 0.10 Å²/ps。对阴影窗口内的均匀采样点作带截距的最小二乘拟合。",
    sliders: [
      ["start", "拟合起点", 0, 25, 1, 0, "ps"],
      ["duration", "窗口宽度", 2, 10, 1, 5, "ps"],
    ],
    presets: [["早期窗口", { start: 0, duration: 5 }], ["晚期窗口", { start: 25, duration: 5 }]],
    compute({ start, duration }) {
      const end = start + duration;
      const msd = t => 6 * 0.1 * (t + 5 * Math.expm1(-t / 5));
      const points = labRange(start, end, 51).map(t => [t, msd(t)]);
      const meanX = (start + end) / 2;
      const meanY = points.reduce((sum, [, y]) => sum + y, 0) / points.length;
      const slope = points.reduce((sum, [x, y]) => sum + (x - meanX) * (y - meanY), 0)
        / points.reduce((sum, [x]) => sum + (x - meanX) ** 2, 0);
      const fit = x => meanY + slope * (x - meanX);
      const variance = points.reduce((sum, [, y]) => sum + (y - meanY) ** 2, 0);
      const residual = points.reduce((sum, [x, y]) => sum + (y - fit(x)) ** 2, 0);
      return {
        x: [0, 35, "时间 t（ps）"], y: [-0.5, 20, "MSD（Å²）"], shade: [start, end],
        lines: [curve(labRange(0, 35), msd, "示意 MSD"),
          curve([start, end], fit, "窗口内线性拟合", 1, "6 3")],
        readings: [["拟合窗口", `${start}–${end} ps`], ["拟合得到 D", `${(slope / 6).toFixed(4)} Å²/ps`],
          ["拟合优度 R²", (1 - residual / variance).toFixed(4)]],
      };
    },
  },
  {
    id: "oer",
    topic: "材料应用 · 07",
    title: "OER 的限制步在哪里切换？",
    short: "OER 过电位",
    note: "材料应用/电催化/电催化描述符与火山图.md",
    formula: "ΔG<sub>O</sub> = 2ΔG<sub>OH</sub>　·　ΔG<sub>OOH</sub> = ΔG<sub>OH</sub> + b　·　η = max(ΔG₁, …, ΔG₄)/e − 1.23 V",
    prompt: "沿过电位曲线从左往右移动，找出限制步切换的位置。降低 b 后，再找谷底并比较最低过电位。",
    detail: "四步依次形成 OH*、O*、OOH* 并释放 O₂，每步转移一个电子，零外加电位时总自由能为 4.92 eV。标度关系采用笔记中的教学模型。",
    sliders: [
      ["oh", "描述符 ΔG₍OH₎", 0.2, 2.6, 0.01, 0.8, "eV"],
      ["offset", "标度关系截距 b", 2.46, 3.6, 0.01, 3.2, "eV"],
    ],
    presets: [["原模型谷底", { oh: 1.6, offset: 3.2 }], ["四步等高", { oh: 1.23, offset: 2.46 }]],
    compute({ oh, offset }) {
      const steps = x => [x, x, offset - x, 4.92 - x - offset];
      const overpotential = x => Math.max(...steps(x)) - 1.23;
      const values = steps(oh);
      const largest = Math.max(...values);
      const limiting = values.flatMap((value, index) => Math.abs(value - largest) < 1e-9 ? [index + 1] : []);
      const eta = Math.max(0, overpotential(oh));
      return {
        x: [0.2, 2.6, "ΔG₍OH₎（eV）"], y: [0, 2.4, "过电位 η（V）"],
        lines: [curve([0.2, offset / 2, 2.6], overpotential, "热力学过电位"), segment(oh, 0, eta)],
        dots: [marker(oh, eta)],
        readings: [["当前过电位", `${displayNumber(eta, 3)} V`], ["热力学限制步", limiting.join("、")],
          ["ΔG₁ 至 ΔG₄（eV）", values.map(value => value.toFixed(2)).join(" / ")]],
      };
    },
  },
];
