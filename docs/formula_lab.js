"use strict";

function html(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svg(tag, attributes, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function ticks(min, max) {
  const rough = (max - min) / 5;
  const unit = 10 ** Math.floor(Math.log10(rough));
  const step = unit * [1, 2, 2.5, 5, 10].find(value => value * unit >= rough);
  const first = Math.ceil(min / step);
  const last = Math.floor(max / step + 1e-9);
  return Array.from({ length: last - first + 1 }, (_, index) => (first + index) * step);
}

function drawChart(chart, model, width, id) {
  const height = Math.max(205, Math.min(310, Math.round(width / 2)));
  const left = 43;
  const right = width - 17;
  const top = 31;
  const bottom = height - 45;
  const [xMin, xMax, xLabel] = model.x;
  const [yMin, yMax, yLabel] = model.y;
  const px = x => left + (x - xMin) / (xMax - xMin) * (right - left);
  const py = y => bottom - (y - yMin) / (yMax - yMin) * (bottom - top);
  const clip = id + "-plot";
  const defs = svg("defs", {});
  const clipPath = svg("clipPath", { id: clip });
  clipPath.append(svg("rect", { x: left, y: top, width: right - left, height: bottom - top }));
  defs.append(clipPath);

  chart.setAttribute("viewBox", `0 0 ${width} ${height}`);
  chart.replaceChildren(svg("title", {}, `${xLabel} 与 ${yLabel}`), defs);

  if (model.shade) {
    const [start, end] = model.shade;
    chart.append(svg("rect", { class: "shade", x: px(start), y: top,
      width: px(end) - px(start), height: bottom - top }));
  }

  for (const value of ticks(xMin, xMax)) {
    const x = px(value);
    chart.append(svg("line", { class: "grid", x1: x, x2: x, y1: top, y2: bottom }),
      svg("text", { x, y: bottom + 17, "text-anchor": "middle" }, displayNumber(value, 3)));
  }
  for (const value of ticks(yMin, yMax)) {
    const y = py(value);
    chart.append(svg("line", { class: "grid", x1: left, x2: right, y1: y, y2: y }),
      svg("text", { x: left - 7, y: y + 4, "text-anchor": "end" }, displayNumber(value, 3)));
  }
  chart.append(svg("path", { class: "axis", fill: "none", d: `M${left} ${top} V${bottom} H${right}` }),
    svg("text", { class: "axis-label", x: left, y: 18 }, yLabel),
    svg("text", { class: "axis-label", x: (left + right) / 2, y: height - 6,
      "text-anchor": "middle" }, xLabel));

  const paths = svg("g", { "clip-path": `url(#${clip})` });
  model.lines.forEach(({ points, label, color, dash, arrow }, index) => {
    const attributes = {
      class: label ? "curve" : "curve guide", stroke: color,
      points: points.map(([x, y]) => `${px(x).toFixed(2)},${py(y).toFixed(2)}`).join(" "),
    };
    if (dash) attributes["stroke-dasharray"] = dash;
    if (arrow) {
      const arrowId = `${id}-arrow-${index}`;
      const tip = svg("marker", { id: arrowId, orient: "auto", viewBox: "0 0 8 8",
        refX: 7, refY: 4, markerWidth: 5, markerHeight: 5 });
      tip.append(svg("path", { d: "M0 0 L8 4 L0 8 Z", fill: color }));
      defs.append(tip);
      attributes["marker-end"] = `url(#${arrowId})`;
    }
    paths.append(svg("polyline", attributes));
  });
  chart.append(paths);
  for (const { x, y, color } of model.dots ?? []) {
    chart.append(svg("circle", { cx: px(x), cy: py(y), r: 4, fill: color }));
  }
}

function buildExperiment(experiment) {
  const { id, title, prompt, detail, formula, note, sliders, presets, compute } = experiment;
  const section = html("section");
  section.id = id;
  section.hidden = true;
  section.setAttribute("aria-labelledby", id + "-title");
  const heading = html("h2", "", title);
  heading.id = id + "-title";
  heading.tabIndex = -1;
  const expression = html("p", "formula");
  expression.innerHTML = formula; // Markup from the experiment definitions only.
  section.append(heading, html("p", "prompt", prompt), expression);

  const chart = svg("svg", { class: "chart", role: "img", "aria-label": title + "的曲线" });
  const legend = html("figcaption", "legend");
  const figure = html("figure");
  figure.append(chart, legend);
  const controls = html("div", "controls");
  const controlHeader = html("div", "control-header");
  const reset = html("button", "reset", "重置");
  reset.type = "button";
  controlHeader.append(html("h3", "", "参数"), reset);
  controls.append(controlHeader);
  const grid = html("div", "lab-grid");
  grid.append(figure, controls);

  const readings = html("dl", "results");
  grid.append(readings);
  const source = html("p", "source");
  const noteLink = html("a", "", "读原笔记");
  noteLink.href = "https://github.com/wangchr1617/research-handbook/blob/main/notes/"
    + note.split("/").map(encodeURIComponent).join("/");
  source.append(noteLink);
  section.append(grid, html("p", "note", detail), source);

  const inputs = sliders.map(([key, name, min, max, step, initial, unit]) => {
    const input = html("input");
    Object.assign(input, { id: id + "-" + key, type: "range", min, max, step, value: initial });
    input.setAttribute("aria-labelledby", input.id + "-label");
    const label = html("label", "control");
    label.htmlFor = input.id;
    const nameNode = html("span", "", name);
    nameNode.id = input.id + "-label";
    const valueNode = html("output");
    valueNode.setAttribute("for", input.id);
    const labelRow = html("span", "control-name");
    labelRow.append(nameNode, valueNode);
    label.append(labelRow, input);
    controls.append(label);
    return { key, input, valueNode, unit, initial };
  });

  let model;
  function redraw() {
    const width = Math.round(figure.clientWidth);
    if (width > 0) drawChart(chart, model, width, id);
  }

  function update() {
    const values = Object.fromEntries(inputs.map(({ key, input, valueNode, unit }) => {
      const shown = [input.value, unit].filter(Boolean).join(" ");
      valueNode.value = shown;
      input.setAttribute("aria-valuetext", shown);
      return [key, input.valueAsNumber];
    }));
    model = compute(values);
    redraw();
    legend.replaceChildren(...model.lines.filter(line => line.label).map(line => {
      const item = html("span");
      const swatch = html("i");
      swatch.style.borderTop = `2px ${line.dash ? "dashed" : "solid"} ${line.color}`;
      item.append(swatch, line.label);
      return item;
    }));
    readings.replaceChildren(...model.readings.map(([label, value]) => {
      const item = html("div");
      item.append(html("dt", "", label), html("dd", "", value));
      return item;
    }));
  }

  const buttons = html("div", "presets");
  const defaults = Object.fromEntries(inputs.map(({ key, initial }) => [key, initial]));
  function setValues(values) {
    for (const { key, input } of inputs) {
      if (Object.hasOwn(values, key)) input.value = values[key];
    }
    update();
  }
  reset.addEventListener("click", () => setValues(defaults));
  for (const [label, values] of presets) {
    const button = html("button", "", label);
    button.type = "button";
    button.addEventListener("click", () => setValues(values));
    buttons.append(button);
  }
  controls.append(buttons);
  for (const { input } of inputs) input.addEventListener("input", update);

  document.querySelector("#lab").append(section);
  update();
  new ResizeObserver(redraw).observe(figure);
  return section;
}

const navigation = document.querySelector("#experiments");
const picker = document.querySelector("#experiment-select");
const panels = experiments.map(experiment => {
  const link = html("a", "", experiment.short);
  link.href = "#" + experiment.id;
  const entry = html("li");
  entry.append(link);
  navigation.append(entry);
  picker.add(new Option(experiment.short, experiment.id));
  return { link, section: buildExperiment(experiment) };
});

function showExperiment(id) {
  const current = panels.find(({ section }) => section.id === id) ?? panels[0];
  for (const panel of panels) {
    panel.section.hidden = panel !== current;
    if (panel === current) panel.link.setAttribute("aria-current", "true");
    else panel.link.removeAttribute("aria-current");
  }
  picker.value = current.section.id;
  return current.section;
}

function navigate(id, focusTitle) {
  const hash = "#" + id;
  if (location.hash !== hash) history.pushState(null, "", hash);
  const section = showExperiment(id);
  if (focusTitle) section.querySelector("h2").focus({ preventScroll: true });
}

for (const { link, section } of panels) {
  link.addEventListener("click", event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigate(section.id, true);
  });
}
picker.addEventListener("change", () => navigate(picker.value, false));
window.addEventListener("hashchange", () => showExperiment(location.hash.slice(1)));

showExperiment(location.hash.slice(1));
navigation.closest("nav").hidden = false;
picker.closest("label").hidden = false;
