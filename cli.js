#!/usr/bin/env node
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const python = findPython();
const script = path.join(__dirname, "tui.py");

if (!python) {
  console.error("\n  Python not found. Install Python first.");
  process.exit(1);
}
if (!fs.existsSync(script)) {
  console.error("\n  tui.py not found alongside cli.js");
  process.exit(1);
}

const proc = spawn(python, [script], {
  stdio: "inherit",
  shell: true,
});

proc.on("exit", (code) => process.exit(code));

function findPython() {
  for (const name of ["python3", "python"]) {
    try {
      const r = spawn.sync(name, ["--version"], { stdio: "pipe" });
      if (r.status === 0) return name;
    } catch {}
  }
  return null;
}
