import { animate as motionAnimate } from "https://cdn.jsdelivr.net/npm/motion@11/+esm";

const form = document.getElementById("ask-form");
const input = document.getElementById("question-input");
const modelSelect = document.getElementById("model-select");
const button = document.getElementById("ask-button");
const statusEl = document.getElementById("status");
const history = document.getElementById("history");
const template = document.getElementById("entry-template");
const historyNav = document.getElementById("history-nav");
const historyNavList = document.getElementById("history-nav-list");

const STORAGE_KEY = "sift_conversation_history";

// Same origin when served locally by FastAPI (app/api/main.py). When this
// page is deployed elsewhere (e.g. Vercel), the backend lives on your Mac
// behind a tunnel — update TUNNEL_URL each time you restart the tunnel.
const TUNNEL_URL = "https://YOUR-TUNNEL-URL.trycloudflare.com";
const API_BASE =
  location.hostname === "localhost" || location.hostname === "http://localhost:8000/"
    ? ""
    : TUNNEL_URL;

function loadStoredEntries() {
  try {
    
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveStoredEntries(entries) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // localStorage unavailable — conversation just won't persist across reloads
  }
}

function arxivLink(arxivId) {
  return `https://arxiv.org/abs/${arxivId}`;
}

function renderMarkdownish(text) {
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const withInline = escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>");

  const blocks = withInline.split(/\n\s*\n/);
  return blocks
    .map((block) => {
      const lines = block.split("\n").filter((l) => l.trim());
      const headingMatch = lines.length === 1 && lines[0].trim().match(/^(#{1,6})\s+(.+)/);
      if (headingMatch) {
        const level = Math.min(headingMatch[1].length + 2, 6); // ## -> h4, keeps below the page's own h1/h2/h3
        return `<h${level}>${headingMatch[2]}</h${level}>`;
      }
      if (lines.every((l) => /^[-*]\s+/.test(l.trim()))) {
        const items = lines.map((l) => `<li>${l.trim().replace(/^[-*]\s+/, "")}</li>`).join("");
        return `<ul>${items}</ul>`;
      }
      return `<p>${block.replace(/\n/g, "<br>")}</p>`;
    })
    .join("");
}

function renderPaperList(listEl, papers) {
  papers.forEach((paper) => {
    const li = document.createElement("li");
    li.classList.add(paper.cited ? "cited" : "found");

    const dot = document.createElement("span");
    dot.classList.add("dot", paper.cited ? "cited" : "found");
    li.appendChild(dot);

    const a = document.createElement("a");
    a.href = arxivLink(paper.arxiv_id);
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = paper.title;
    li.appendChild(a);

    listEl.appendChild(li);
  });
}

function renderMindmap(svg, question, papers, animated) {
  const cx = 300;
  const cy = 250;
  const radius = Math.min(200, 60 + papers.length * 12);

  const centerCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  centerCircle.setAttribute("cx", cx);
  centerCircle.setAttribute("cy", cy);
  centerCircle.setAttribute("r", 8);
  centerCircle.setAttribute("fill", "#7c9eff");
  centerCircle.classList.add("node-circle");
  svg.appendChild(centerCircle);

  const centerLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
  centerLabel.setAttribute("x", cx);
  centerLabel.setAttribute("y", cy - 16);
  centerLabel.setAttribute("text-anchor", "middle");
  centerLabel.classList.add("node-label", "center");
  const shortQ = question.length > 40 ? question.slice(0, 40) + "…" : question;
  centerLabel.textContent = shortQ;
  svg.appendChild(centerLabel);

  const nodeEls = [];
  const lineEls = [];
  const labelEls = [];

  papers.forEach((paper, i) => {
    const angle = (i / papers.length) * Math.PI * 2 - Math.PI / 2;
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", cx);
    line.setAttribute("y1", cy);
    line.setAttribute("x2", x);
    line.setAttribute("y2", y);
    line.classList.add("edge");
    svg.appendChild(line);
    lineEls.push(line);

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", x);
    circle.setAttribute("cy", y);
    circle.setAttribute("r", 6);
    circle.setAttribute("fill", paper.cited ? "#6ee7b7" : "#4b5163");
    circle.classList.add("node-circle");
    circle.style.transformOrigin = `${x}px ${y}px`;
    svg.appendChild(circle);
    nodeEls.push(circle);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    const dx = Math.cos(angle) >= 0 ? 10 : -10;
    label.setAttribute("x", x + dx);
    label.setAttribute("y", y + 4);
    label.setAttribute("text-anchor", Math.cos(angle) >= 0 ? "start" : "end");
    label.classList.add("node-label");
    const shortTitle = paper.title.length > 38 ? paper.title.slice(0, 38) + "…" : paper.title;
    label.textContent = shortTitle;
    svg.appendChild(label);
    labelEls.push(label);

    circle.addEventListener("pointerenter", () => {
      motionAnimate(circle, { scale: 1.6 }, { type: "spring", stiffness: 400, damping: 15 });
    });
    circle.addEventListener("pointerleave", () => {
      motionAnimate(circle, { scale: 1 }, { type: "spring", stiffness: 400, damping: 15 });
    });
    circle.addEventListener("click", () => {
      window.open(arxivLink(paper.arxiv_id), "_blank", "noopener,noreferrer");
    });
  });

  if (!animated) {
    // rehydrated from storage — render statically, skip the entrance animation
    nodeEls.forEach((el) => (el.style.transform = "scale(1)"));
    labelEls.forEach((el) => (el.style.opacity = "1"));
    return;
  }

  lineEls.forEach((line) => {
    const length = Math.hypot(
      line.x2.baseVal.value - line.x1.baseVal.value,
      line.y2.baseVal.value - line.y1.baseVal.value
    );
    line.style.strokeDasharray = length;
    line.style.strokeDashoffset = length;
  });

  anime.timeline({ easing: "easeOutExpo" })
    .add({ targets: centerCircle, scale: [0, 1], duration: 400 })
    .add(
      {
        targets: lineEls,
        strokeDashoffset: [anime.setDashoffset, 0],
        duration: 500,
        delay: anime.stagger(60),
      },
      "-=200"
    )
    .add(
      {
        targets: nodeEls,
        scale: [0, 1],
        duration: 400,
        delay: anime.stagger(60),
        easing: "easeOutElastic(1, 0.6)",
      },
      "-=400"
    )
    .add(
      { targets: labelEls, opacity: [0, 1], duration: 300, delay: anime.stagger(40) },
      "-=300"
    );
}

function renderEntry(record, index, animated) {
  const entry = template.content.firstElementChild.cloneNode(true);
  entry.id = `entry-${index}`;
  entry.querySelector(".entry-question").textContent = record.question;

  const answerText = entry.querySelector(".answer-text");
  answerText.innerHTML = renderMarkdownish(record.answer || "(no answer)");

  const metaBits = [
    `${record.iterations_used ?? "?"} iterations`,
    `${record.total_tokens ?? "?"} tokens`,
    `${record.total_latency ? record.total_latency.toFixed(1) + "s" : "?"}`,
  ];
  if (record.incomplete) metaBits.push("⚠ hit iteration cap");
  entry.querySelector(".meta").textContent = metaBits.join("  ·  ");

  history.appendChild(entry);

  const svg = entry.querySelector(".mindmap");
  renderMindmap(svg, record.question, record.papers || [], animated);
  renderPaperList(entry.querySelector(".paper-list"), record.papers || []);

  return entry;
}

function addHistoryNavItem(question, index) {
  historyNav.hidden = false;
  const li = document.createElement("li");
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = question;
  btn.addEventListener("click", () => {
    document.getElementById(`entry-${index}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  li.appendChild(btn);
  historyNavList.appendChild(li);
}

// rehydrate from localStorage on load
const storedEntries = loadStoredEntries();
storedEntries.forEach((record, i) => {
  renderEntry(record, i, false);
  addHistoryNavItem(record.question, i);
});
if (storedEntries.length) {
  requestAnimationFrame(() => {
    document.getElementById(`entry-${storedEntries.length - 1}`)?.scrollIntoView({ block: "start" });
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  button.disabled = true;
  statusEl.hidden = false;
  statusEl.classList.remove("error");
  statusEl.textContent = "Thinking…";
  input.value = "";

  try {
    const res = await fetch(`${API_BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, model: modelSelect.value }),
    });

    if (!res.ok) throw new Error(`Server error (${res.status})`);
    const data = await res.json();

    const entries = loadStoredEntries();
    const index = entries.length;
    entries.push(data);
    saveStoredEntries(entries);

    statusEl.hidden = true;
    const entry = renderEntry(data, index, true);
    addHistoryNavItem(question, index);
    entry.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    statusEl.classList.add("error");
    statusEl.textContent = `Something went wrong: ${err.message}`;
  } finally {
    button.disabled = false;
  }
});
