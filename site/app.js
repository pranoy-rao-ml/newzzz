const REFRESH_MS = 5 * 60 * 1000;
const LABELS = {
  top: "Top", world: "World", business: "Business", technology: "Tech",
  science: "Science", health: "Health", culture: "Culture", sport: "Sport",
};

let data = null;
let current = new URLSearchParams(location.search).get("category") || "top";

const $ = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function safeUrl(u) {
  try {
    const url = new URL(u);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : "#";
  } catch { return "#"; }
}

function timeAgo(iso) {
  const secs = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function renderCategories() {
  $("categories").innerHTML = data.categories.map((c) => {
    const active = c === current;
    const cls = active
      ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
      : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
    return `<button data-cat="${c}" aria-pressed="${active}"
      class="shrink-0 px-3 py-1.5 rounded-full text-sm font-medium ${cls}">${LABELS[c] || c}</button>`;
  }).join("");
}

function renderStory(s) {
  const also = s.also.length
    ? `<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">Also covered by ${s.also
        .map((a) => `<a class="underline" href="${safeUrl(a.url)}" target="_blank" rel="noopener">${escapeHtml(a.source)}</a>`)
        .join(", ")}</p>`
    : "";
  const img = s.image
    ? `<img src="${safeUrl(s.image)}" alt="" loading="lazy" class="w-20 h-20 sm:w-28 sm:h-20 object-cover rounded-lg shrink-0 bg-slate-200 dark:bg-slate-800" onerror="this.remove()">`
    : "";
  return `<li class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
    <div class="flex gap-3">
      <div class="min-w-0 flex-1">
        <p class="text-xs text-slate-500 dark:text-slate-400">
          <span class="font-medium text-slate-700 dark:text-slate-300">${escapeHtml(s.source)}</span>
          · <time datetime="${escapeHtml(s.published_at)}">${timeAgo(s.published_at)}</time>
        </p>
        <h2 class="mt-1 font-semibold leading-snug">
          <a href="${safeUrl(s.url)}" target="_blank" rel="noopener" class="hover:underline">${escapeHtml(s.title)}</a>
        </h2>
      </div>
      ${img}
    </div>
    ${s.summary ? `<p class="mt-2 text-sm text-slate-600 dark:text-slate-300 line-clamp-3">${escapeHtml(s.summary)}</p>` : ""}
    ${also}
  </li>`;
}

function render() {
  if (!data.stories[current]) current = "top";
  renderCategories();
  const stories = data.stories[current] || [];
  $("stories").innerHTML = stories.map(renderStory).join("");
  $("status").textContent = stories.length ? "" : "No stories right now.";
  $("status").hidden = stories.length > 0;
  $("updated").textContent = `Updated ${timeAgo(data.generated_at)}`;
  $("sources").textContent = `Sources: ${data.sources.join(", ")}. Headlines and summaries belong to their publishers.`;
}

async function load() {
  try {
    const res = await fetch(`news.json?t=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
    render();
  } catch (err) {
    if (!data) $("status").textContent = "Couldn't load the news. Pull to refresh or try again shortly.";
  }
}

$("categories").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-cat]");
  if (!btn) return;
  current = btn.dataset.cat;
  const url = new URL(location);
  if (current === "top") url.searchParams.delete("category");
  else url.searchParams.set("category", current);
  history.replaceState(null, "", url);
  render();
  window.scrollTo({ top: 0 });
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") load();
});

load();
setInterval(load, REFRESH_MS);
