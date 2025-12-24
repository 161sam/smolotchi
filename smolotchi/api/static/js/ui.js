function setActiveTab(root, tabId) {
  const tabs = root.querySelectorAll("[data-tab]");
  const panes = root.querySelectorAll("[data-pane]");
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabId));
  panes.forEach((pane) => {
    pane.style.display = pane.dataset.pane === tabId ? "block" : "none";
  });
  localStorage.setItem(root.dataset.tabsKey, tabId);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-tabs]").forEach((root) => {
    const key = root.dataset.tabsKey || "tabs";
    root.dataset.tabsKey = key;
    const defaultTab = root.dataset.defaultTab || "meta";
    const saved = localStorage.getItem(key);
    const tab = saved || defaultTab;
    setActiveTab(root, tab);

    root.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => setActiveTab(root, btn.dataset.tab));
    });
  });

  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const targetId = btn.dataset.copy;
      const el = document.getElementById(targetId);
      if (!el) return;
      const text = el.innerText || el.value || "";
      try {
        await navigator.clipboard.writeText(text);
        btn.innerText = "Copied ✓";
        setTimeout(() => {
          btn.innerText = "Copy";
        }, 1200);
      } catch {
        btn.innerText = "Copy failed";
        setTimeout(() => {
          btn.innerText = "Copy";
        }, 1200);
      }
    });
  });

  document.querySelectorAll("[data-collapse]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sel = btn.dataset.collapse;
      const el = document.querySelector(sel);
      if (!el) return;
      const isHidden = el.style.display === "none";
      el.style.display = isHidden ? "block" : "none";
      btn.innerText = isHidden ? "Hide" : "Show";
    });
  });
});
