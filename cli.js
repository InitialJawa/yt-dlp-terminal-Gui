#!/usr/bin/env node
const { spawn, spawnSync, execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const readline = require("readline");

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = (q) => new Promise((r) => rl.question(q, r));

async function main() {
  const script = path.join(__dirname, "tui.py");

  if (!fs.existsSync(script)) {
    console.error("\n  tui.py not found alongside cli.js");
    process.exit(1);
  }

  let python = findPython();
  if (!python) {
    console.log("\n  \x1b[33mPython not found.\x1b[0m");
    const ans = await ask("  Install Python via winget? (Y/n): ");
    if (ans.toLowerCase() !== "n") {
      console.log("  Installing Python...");
      const r = spawnSync("winget", ["install", "Python.Python", "--accept-package-agreements", "--accept-source-agreements"], { stdio: "inherit", shell: true });
      if (r.status !== 0) {
        console.log("\n  \x1b[31mInstall failed. Install Python manually from https://python.org\x1b[0m");
        process.exit(1);
      }
      python = findPython();
      if (!python) {
        console.log("\n  \x1b[31mPython still not found. Restart terminal and try again.\x1b[0m");
        process.exit(1);
      }
    } else {
      process.exit(1);
    }
  }

  let ytdlp = findYtdlp();
  if (!ytdlp) {
    console.log("\n  \x1b[33myt-dlp not found.\x1b[0m");
    const ans = await ask("  Install yt-dlp? (Y/n): ");
    if (ans.toLowerCase() !== "n") {
      console.log("  Installing yt-dlp via pip...");
      spawnSync(python, ["-m", "pip", "install", "-U", "yt-dlp"], { stdio: "inherit", shell: true });
      ytdlp = findYtdlp();
      if (!ytdlp) {
        console.log("\n  \x1b[33mTrying winget...\x1b[0m");
        spawnSync("winget", ["install", "yt-dlp.yt-dlp", "--accept-package-agreements", "--accept-source-agreements"], { stdio: "inherit", shell: true });
        ytdlp = findYtdlp();
      }
      if (!ytdlp) {
        console.log("\n  \x1b[31myt-dlp install failed. Restart terminal and try again.\x1b[0m");
        process.exit(1);
      }
    } else {
      process.exit(1);
    }
  }

  rl.close();

  const proc = spawn(python, [script], { stdio: "inherit", shell: true });
  proc.on("exit", (code) => process.exit(code));
}

function findPython() {
  for (const name of ["python3", "python"]) {
    try {
      const r = spawnSync(name, ["--version"], { stdio: "pipe" });
      if (r.status === 0) return name;
    } catch {}
  }
  return null;
}

function findYtdlp() {
  try {
    const r = spawnSync("yt-dlp", ["--version"], { stdio: "pipe" });
    if (r.status === 0) return true;
  } catch {}
  return null;
}

main();
