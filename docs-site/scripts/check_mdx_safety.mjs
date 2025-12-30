import { readdir, readFile } from "node:fs/promises";

const META_DIR = new URL("../docs/_meta/", import.meta.url);
const MDX_JSX_RE = /<(?=[A-Za-z])/;

const files = (await readdir(META_DIR)).filter((name) => name.endsWith(".md"));
const failures = [];

for (const name of files) {
  const fileUrl = new URL(name, META_DIR);
  const content = await readFile(fileUrl, "utf8");
  const lines = content.split(/\r?\n/);
  let inFence = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim().startsWith("```")) {
      inFence = !inFence;
      continue;
    }
    if (inFence) {
      continue;
    }

    if (MDX_JSX_RE.test(line)) {
      failures.push(`${name}:${index + 1} contains raw '<' that looks like JSX`);
    }
    if (line.includes("{") || line.includes("}")) {
      failures.push(`${name}:${index + 1} contains raw '{' or '}'`);
    }
  }
}

if (failures.length) {
  console.error("MDX safety check failed:\n" + failures.join("\n"));
  process.exit(1);
}

console.log(`MDX safety check passed for ${files.length} _meta docs.`);
