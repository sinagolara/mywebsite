"use strict";

const root = document.documentElement;
const sectionAliases = new Map([
  ["#research", "research/"],
  ["#teaching", "teaching/"],
  ["#media", "media/"]
]);

if (document.body.dataset.page === "home") {
  function forwardLegacyLink() {
    const page = sectionAliases.get(location.hash.split("?")[0]);
    if (page) location.replace(new URL(page, location.href));
  }

  forwardLegacyLink();
  window.addEventListener("hashchange", forwardLegacyLink);
}

const themeButton = document.querySelector(".theme-toggle");
const systemTheme = matchMedia("(prefers-color-scheme: dark)");
let savedTheme;
try {
  savedTheme = localStorage.getItem("theme");
} catch {
  savedTheme = null;
}

function applyTheme(dark) {
  root.dataset.theme = dark ? "dark" : "light";
  themeButton.setAttribute("aria-pressed", String(dark));
}

applyTheme(savedTheme === "dark" || (savedTheme !== "light" && systemTheme.matches));
themeButton.hidden = false;
themeButton.addEventListener("click", () => {
  const dark = root.dataset.theme !== "dark";
  savedTheme = dark ? "dark" : "light";
  applyTheme(dark);
  try {
    localStorage.setItem("theme", savedTheme);
  } catch {
    // The theme still works for this page when storage is unavailable.
  }
});
systemTheme.addEventListener("change", (event) => {
  if (savedTheme !== "light" && savedTheme !== "dark") applyTheme(event.matches);
});

const mobile = matchMedia("(max-width: 47.99rem)");
const menuButton = document.querySelector(".menu-toggle");
const nav = document.getElementById("site-nav");

function setMenu(open) {
  const expanded = mobile.matches && open;
  nav.hidden = mobile.matches && !expanded;
  menuButton.setAttribute("aria-expanded", String(expanded));
  menuButton.textContent = expanded ? "Close" : "Menu";
}

menuButton.hidden = false;
setMenu(false);
menuButton.addEventListener("click", () => setMenu(nav.hidden));
mobile.addEventListener("change", () => setMenu(false));
nav.addEventListener("click", (event) => {
  if (event.target.closest("a") && mobile.matches) setMenu(false);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
    setMenu(false);
    menuButton.focus();
  }
});

function compareOldestFirst(a, b) {
  // Items with no verified date follow dated items in either direction.
  if (!a.dataset.sort || !b.dataset.sort) {
    return Number(!a.dataset.sort) - Number(!b.dataset.sort);
  }
  return a.dataset.sort.localeCompare(b.dataset.sort);
}

const sortButton = document.querySelector(".chronological-sort");
if (sortButton) {
  const list = document.getElementById(sortButton.getAttribute("aria-controls"));
  const status = document.getElementById(list.id + "-sort-status");
  const label = sortButton.dataset.sortLabel;
  const newest = Array.from(list.children);
  const oldest = [...newest].sort(compareOldestFirst);

  sortButton.hidden = false;
  sortButton.addEventListener("click", () => {
    const showOldest = sortButton.dataset.order === "newest";
    list.append(...(showOldest ? oldest : newest));
    sortButton.dataset.order = showOldest ? "oldest" : "newest";
    const nextOrder = showOldest ? "newest first" : "oldest first";
    sortButton.setAttribute("aria-label", "Sort " + label.toLowerCase() + " " + nextOrder);
    sortButton.title = "Sort " + nextOrder;
    status.textContent = label + " sorted " + (showOldest ? "oldest first." : "newest first.");
  });
}
