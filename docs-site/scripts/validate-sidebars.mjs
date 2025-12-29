import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const docsRoot = path.join(__dirname, "..", "docs");

const require = createRequire(import.meta.url);
const sidebars = require(path.join(__dirname, "..", "sidebars.js"));

const DOC_EXTENSIONS = new Set([".md", ".mdx"]);

const readDocId = (filePath) => {
  const relativePath = path
    .relative(docsRoot, filePath)
    .replace(/\\/g, "/");
  const ext = path.extname(relativePath);
  const defaultId = relativePath.slice(0, -ext.length);

  const content = fs.readFileSync(filePath, "utf8");
  if (content.startsWith("---")) {
    const end = content.indexOf("\n---", 3);
    if (end !== -1) {
      const frontmatter = content.slice(3, end).split("\n");
      const idLine = frontmatter.find((line) => line.trim().startsWith("id:"));
      if (idLine) {
        const [, idValue] = idLine.split(":");
        if (idValue) {
          return idValue.trim().replace(/^['"]|['"]$/g, "");
        }
      }
    }
  }

  return defaultId;
};

const collectDocIds = (root) => {
  const ids = new Set();
  const stack = [root];
  while (stack.length > 0) {
    const current = stack.pop();
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const entryPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(entryPath);
        continue;
      }
      if (!DOC_EXTENSIONS.has(path.extname(entry.name))) {
        continue;
      }
      ids.add(readDocId(entryPath));
    }
  }
  return ids;
};

const collectSidebarDocIds = (items, collected = []) => {
  for (const item of items) {
    if (typeof item === "string") {
      collected.push(item);
      continue;
    }
    if (!item || typeof item !== "object") {
      continue;
    }
    if (item.type === "doc" && typeof item.id === "string") {
      collected.push(item.id);
    }
    if (Array.isArray(item.items)) {
      collectSidebarDocIds(item.items, collected);
    }
  }
  return collected;
};

const docIds = collectDocIds(docsRoot);
const sidebarDocIds = collectSidebarDocIds(sidebars.docsSidebar ?? []);

const missing = sidebarDocIds.filter((id) => !docIds.has(id));
if (missing.length > 0) {
  console.error("Sidebar references missing doc ids:");
  for (const id of missing) {
    console.error(`- ${id}`);
  }
  process.exit(1);
}

console.log("Sidebar validation passed.");
