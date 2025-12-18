#!/usr/bin/env node
/**
 * AInfluencer Unified Launcher - Canonical Cross-Platform Orchestrator
 *
 * This is the ONE canonical startup script. All wrappers (launch.bat, launch.command, launch.sh)
 * should call this script. It handles:
 * - Doctor/preflight checks
 * - Backend venv and dependency management
 * - Frontend dependency management
 * - Port selection with fallback
 * - Service startup with health checks
 * - Structured logging
 * - Browser opening
 * - Diagnose and stop commands
 */

import { spawn, exec } from "child_process";
import { promisify } from "util";
import {
  writeFile,
  mkdir,
  readFile,
  readdir,
  stat,
  access,
  constants,
} from "fs/promises";
import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";
import { existsSync } from "fs";

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = resolve(__dirname, "..");

// Parse command line arguments
const args = process.argv.slice(2);
const isDiagnose = args.includes("--diagnose");
const isStop = args.includes("--stop");
const isDoctor = args.includes("--doctor");
const isWithTTS = args.includes("--with-tts");

// Setup run directory
const timestamp = new Date()
  .toISOString()
  .replace(/[:.]/g, "-")
  .slice(0, 19)
  .replace("T", "_");
const RUNS_DIR = join(ROOT_DIR, "runs", "launcher");
const RUN_DIR = join(RUNS_DIR, timestamp);
const LATEST_FILE = join(RUNS_DIR, "latest.txt");
const AINFLUENCER_DIR = join(ROOT_DIR, ".ainfluencer");
const BACKEND_PID_FILE = join(AINFLUENCER_DIR, "backend.pid");
const FRONTEND_PID_FILE = join(AINFLUENCER_DIR, "frontend.pid");

// Log files
const BACKEND_STDOUT_LOG = join(RUN_DIR, "backend.stdout.log");
const BACKEND_STDERR_LOG = join(RUN_DIR, "backend.stderr.log");
const FRONTEND_STDOUT_LOG = join(RUN_DIR, "frontend.stdout.log");
const FRONTEND_STDERR_LOG = join(RUN_DIR, "frontend.stderr.log");
const DOCTOR_LOG = join(RUN_DIR, "doctor.log");
const PORTS_FILE = join(RUN_DIR, "ports.json");
const RUN_SUMMARY_JSON = join(RUN_DIR, "run_summary.json");
const ERROR_ROOT_CAUSE_JSON = join(RUN_DIR, "error_root_cause.json");
const EVENTS_FILE = join(RUN_DIR, "events.jsonl");

// State
let backendPid = null;
let frontendPid = null;
let backendPort = null;
let frontendPort = null;

// Utility functions
function log(level, service, message, fix = null) {
  const event = {
    ts: Math.floor(Date.now() / 1000),
    level,
    service,
    message,
    ...(fix && { fix }),
  };

  const timestamp = new Date().toISOString().replace("T", " ").slice(0, 19);
  const color =
    level === "error"
      ? "\x1b[31m"
      : level === "warning"
      ? "\x1b[33m"
      : "\x1b[0m";
  const reset = "\x1b[0m";

  console.log(
    `${color}[${timestamp}] [${level}] [${service}] ${message}${reset}`
  );

  // Write to events.jsonl
  writeFile(EVENTS_FILE, JSON.stringify(event) + "\n", { flag: "a" }).catch(
    () => {}
  );
}

async function ensureDir(dir) {
  try {
    await mkdir(dir, { recursive: true });
  } catch (err) {
    // Ignore if exists
  }
}

async function writeJsonFile(path, data) {
  await writeFile(path, JSON.stringify(data, null, 2) + "\n", "utf8");
}

function isWindows() {
  return process.platform === "win32";
}

function isMac() {
  return process.platform === "darwin";
}

// Check for CRLF line endings in shell scripts (macOS/Linux issue)
async function checkScriptLineEndings(scriptPath) {
  if (isWindows()) {
    return; // CRLF is fine on Windows
  }

  try {
    const content = await readFile(scriptPath, "utf8");
    if (content.includes("\r\n")) {
      log(
        "warning",
        "launcher",
        `Script ${scriptPath} has CRLF line endings. This may cause issues on macOS/Linux.`
      );
      log(
        "warning",
        "launcher",
        `Fix with: dos2unix "${scriptPath}" or: sed -i '' 's/\r$//' "${scriptPath}"`
      );
    }
  } catch (err) {
    // Ignore read errors
  }
}

// Doctor/preflight checks
async function runDoctor() {
  log("info", "launcher", "Running doctor checks...");

  const doctorScript = isWindows()
    ? join(ROOT_DIR, "scripts", "doctor.ps1")
    : join(ROOT_DIR, "scripts", "doctor.sh");

  if (!existsSync(doctorScript)) {
    log(
      "warning",
      "launcher",
      "Doctor script not found, running inline checks"
    );
    return await runInlineChecks();
  }

  // Check for CRLF line endings on macOS/Linux
  await checkScriptLineEndings(doctorScript);

  try {
    const cmd = isWindows()
      ? `powershell.exe -ExecutionPolicy Bypass -File "${doctorScript}"`
      : `bash "${doctorScript}"`;

    const { stdout, stderr } = await execAsync(cmd, { cwd: ROOT_DIR });
    await writeFile(DOCTOR_LOG, stdout + stderr, "utf8");

    // Doctor script exits with non-zero on failure, which execAsync will throw
    // If we get here, doctor passed
    log("info", "launcher", "Doctor checks passed");
    return true;
  } catch (err) {
    // Read doctor log to provide better error message
    let doctorOutput = "";
    try {
      doctorOutput = await readFile(DOCTOR_LOG, "utf8");
    } catch {}

    // Check if doctor failed due to Python 3.11 missing on macOS
    // In that case, we can auto-install, so fall back to inline checks
    const isPython311Missing = doctorOutput.includes("Python 3.11 not found");
    const canAutoInstall =
      isMac() && doctorOutput.includes("will be auto-installed");

    if (isPython311Missing && canAutoInstall) {
      log(
        "warning",
        "launcher",
        "Doctor check: Python 3.11 not found, but can auto-install. Falling back to inline checks..."
      );
      // Fall through to inline checks which will handle auto-install
      return await runInlineChecks();
    }

    log("error", "launcher", `Doctor checks failed: ${err.message}`);
    if (doctorOutput) {
      // Extract FAIL lines and critical issues
      const failLines = doctorOutput
        .split("\n")
        .filter(
          (line) => line.includes("[FAIL]") || line.includes("Critical issues")
        )
        .slice(0, 10);

      if (failLines.length > 0) {
        console.log("\n=== Doctor Check Failures ===");
        failLines.forEach((line) => console.log(line));
        console.log("");
      }
    }

    throw new Error(
      "Doctor checks failed. Review output above and fix issues before launching."
    );
  }
}

// Find Python 3.11 for backend (canonical version)
async function findPython311() {
  // Check for override environment variable
  const overridePython = process.env.AINFLUENCER_PYTHON;
  if (overridePython) {
    try {
      const { stdout } = await execAsync(`"${overridePython}" --version`);
      const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1].split(".")[0], 10);
        const minor = parseInt(versionMatch[1].split(".")[1], 10);
        if (major === 3 && minor === 11) {
          log(
            "info",
            "launcher",
            `Using override Python: ${overridePython} (${versionMatch[1]})`
          );
          return { cmd: overridePython, version: versionMatch[1] };
        } else {
          log(
            "warning",
            "launcher",
            `Override Python ${overridePython} is not 3.11 (found ${versionMatch[1]}), ignoring`
          );
        }
      }
    } catch (err) {
      log(
        "warning",
        "launcher",
        `Override Python ${overridePython} not valid, ignoring: ${err.message}`
      );
    }
  }

  if (isWindows()) {
    // Windows: Try py launcher with 3.11 first
    try {
      const { stdout } = await execAsync(`py -3.11 --version`);
      const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1].split(".")[0], 10);
        const minor = parseInt(versionMatch[1].split(".")[1], 10);
        if (major === 3 && minor === 11) {
          return { cmd: "py -3.11", version: versionMatch[1] };
        }
      }
    } catch {}

    // Fallback to python command
    try {
      const { stdout } = await execAsync("python --version");
      const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1].split(".")[0], 10);
        const minor = parseInt(versionMatch[1].split(".")[1], 10);
        if (major === 3 && minor === 11) {
          return { cmd: "python", version: versionMatch[1] };
        }
      }
    } catch {}

    throw new Error(
      "Python 3.11 not found. Install Python 3.11 from python.org"
    );
  } else {
    // macOS/Linux: Try python3.11 first
    try {
      const { stdout } = await execAsync("python3.11 --version");
      const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1].split(".")[0], 10);
        const minor = parseInt(versionMatch[1].split(".")[1], 10);
        if (major === 3 && minor === 11) {
          return { cmd: "python3.11", version: versionMatch[1] };
        }
      }
    } catch {}

    // macOS: Try to auto-install via Homebrew
    if (isMac()) {
      try {
        // Check if brew is available
        await execAsync("which brew");
        log(
          "info",
          "launcher",
          "Homebrew detected, attempting to install python@3.11..."
        );

        try {
          await execAsync("brew install python@3.11", { timeout: 300000 }); // 5 min timeout
          log("info", "launcher", "Python 3.11 installed via Homebrew");

          // Try again after install
          const { stdout } = await execAsync("python3.11 --version");
          const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
          if (versionMatch) {
            const major = parseInt(versionMatch[1].split(".")[0], 10);
            const minor = parseInt(versionMatch[1].split(".")[1], 10);
            if (major === 3 && minor === 11) {
              return { cmd: "python3.11", version: versionMatch[1] };
            }
          }
        } catch (brewErr) {
          log(
            "warning",
            "launcher",
            `Homebrew install failed: ${brewErr.message}`
          );
          log(
            "warning",
            "launcher",
            "You may need to run manually: brew install python@3.11"
          );
        }
      } catch (brewCheckErr) {
        // Homebrew not available, continue to error
      }
    }

    // Check what Python versions are available for better error message
    const availableVersions = [];
    for (const cmd of [
      "python3.13",
      "python3.12",
      "python3.11",
      "python3",
      "python",
    ]) {
      try {
        const { stdout } = await execAsync(`${cmd} --version 2>&1`);
        const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
        if (versionMatch) {
          availableVersions.push(`${cmd} (${versionMatch[1]})`);
        }
      } catch {}
    }

    const availableMsg =
      availableVersions.length > 0
        ? ` Found: ${availableVersions.join(", ")}`
        : "";

    if (isMac()) {
      throw new Error(
        `Python 3.11 not found.${availableMsg} Install with: brew install python@3.11`
      );
    } else {
      throw new Error(
        `Python 3.11 not found.${availableMsg} Install Python 3.11 from python.org or your package manager`
      );
    }
  }
}

async function runInlineChecks() {
  // Check Python - MUST be 3.11 for backend (canonical version)
  let pythonCmd = null;
  let pythonVersion = null;

  try {
    const pythonInfo = await findPython311();
    pythonCmd = pythonInfo.cmd;
    pythonVersion = pythonInfo.version;
    log("info", "launcher", `Python found: ${pythonCmd} (${pythonVersion})`);
  } catch (err) {
    log("error", "launcher", err.message);
    throw err;
  }

  // Check Node.js
  try {
    const { stdout } = await execAsync("node --version");
    log("info", "launcher", `Node.js found: ${stdout.trim()}`);
  } catch (err) {
    log("error", "launcher", "Node.js not found. Install Node.js LTS.");
    throw err;
  }

  // Check npm
  try {
    const { stdout } = await execAsync("npm --version");
    log("info", "launcher", `npm found: ${stdout.trim()}`);
  } catch (err) {
    log(
      "error",
      "launcher",
      "npm not found. Reinstall Node.js (npm comes with Node.js)."
    );
    throw err;
  }

  return true;
}

// Port management
async function testPort(port) {
  try {
    if (isWindows()) {
      const { stdout } = await execAsync(`netstat -ano | findstr ":${port} "`);
      return stdout.trim().length > 0;
    } else {
      const { stdout } = await execAsync(`lsof -ti:${port} || true`);
      return stdout.trim().length > 0;
    }
  } catch {
    return false;
  }
}

async function getPortPid(port) {
  try {
    if (isWindows()) {
      const { stdout } = await execAsync(`netstat -ano | findstr ":${port} "`);
      const lines = stdout.trim().split("\n");
      if (lines.length > 0) {
        const parts = lines[0].trim().split(/\s+/);
        const pid = parts[parts.length - 1];
        if (/^\d+$/.test(pid)) {
          return parseInt(pid, 10);
        }
      }
    } else {
      const { stdout } = await execAsync(`lsof -ti:${port}`);
      const pid = stdout.trim();
      if (/^\d+$/.test(pid)) {
        return parseInt(pid, 10);
      }
    }
  } catch {}
  return null;
}

async function checkHealth(url, maxWait = 60) {
  const startTime = Date.now();
  const interval = 2000; // 2 seconds
  let attempt = 0;

  while (Date.now() - startTime < maxWait * 1000) {
    attempt++;
    try {
      // Use curl/http for health check (more reliable cross-platform)
      const cmd = isWindows()
        ? `powershell -Command "try { $response = Invoke-WebRequest -Uri '${url}' -Method Get -TimeoutSec 2 -UseBasicParsing; exit $response.StatusCode } catch { exit 1 }"`
        : `curl -s -f -o /dev/null -w "%{http_code}" "${url}" || echo "000"`;

      const { stdout } = await execAsync(cmd, { timeout: 3000 });
      const statusCode = isWindows()
        ? parseInt(stdout.trim(), 10)
        : parseInt(stdout.trim(), 10);

      if (statusCode >= 200 && statusCode < 400) {
        log("info", "launcher", `Health check passed (attempt ${attempt})`);
        return true;
      }
    } catch (err) {
      // Continue waiting
    }

    if (attempt % 5 === 0) {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      log(
        "info",
        "launcher",
        `Waiting for health check... (${elapsed}/${maxWait} seconds, attempt ${attempt})`
      );
    }

    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  return false;
}

async function getAvailablePort(ports, serviceName) {
  // Validate ports array
  if (!Array.isArray(ports) || ports.length === 0) {
    throw new Error(
      `Invalid ports array for ${serviceName}: must be non-empty array`
    );
  }

  // Ensure all ports are valid numbers
  const validPorts = ports.filter(
    (p) => typeof p === "number" && p > 0 && p < 65536
  );
  if (validPorts.length === 0) {
    throw new Error(`No valid ports found for ${serviceName}`);
  }

  for (const port of validPorts) {
    const inUse = await testPort(port);
    if (!inUse) {
      log(
        "info",
        "launcher",
        `Selected port ${port} for ${serviceName} (available)`
      );
      return { port, pid: null, reused: false };
    }

    // Check if it's our process
    const pid = await getPortPid(port);
    if (pid) {
      // Test health
      const healthUrl =
        serviceName === "backend"
          ? `http://localhost:${port}/api/health`
          : `http://localhost:${port}`;

      if (await checkHealth(healthUrl, 2)) {
        log(
          "info",
          "launcher",
          `Reusing existing ${serviceName} on port ${port} (PID: ${pid}, healthy)`
        );
        return { port, pid, reused: true };
      }
    }
  }

  // No available port, use first valid port (will attempt to bind, may fail)
  const selectedPort = validPorts[0];
  log(
    "warning",
    "launcher",
    `No available ports found for ${serviceName}, using ${selectedPort} (may be in use)`
  );
  return { port: selectedPort, pid: null, reused: false };
}

// Backend management
async function ensureBackendVenv(forceRecreate = false) {
  const backendDir = join(ROOT_DIR, "backend");
  const venvDir = join(backendDir, ".venv");
  const venvPython = isWindows()
    ? join(venvDir, "Scripts", "python.exe")
    : join(venvDir, "bin", "python");

  // Check if venv exists and verify Python version
  if (existsSync(venvPython)) {
    try {
      const { stdout } = await execAsync(`"${venvPython}" --version`);
      const versionMatch = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (versionMatch) {
        const major = parseInt(versionMatch[1].split(".")[0], 10);
        const minor = parseInt(versionMatch[1].split(".")[1], 10);
        if (major !== 3 || minor !== 11) {
          log(
            "warning",
            "backend",
            `Existing venv uses Python ${versionMatch[1]} (requires 3.11), recreating...`
          );
          forceRecreate = true;
        }
      }
    } catch (err) {
      // If we can't check version, assume it's wrong and recreate
      log(
        "warning",
        "backend",
        "Cannot verify venv Python version, recreating..."
      );
      forceRecreate = true;
    }
  }

  if (forceRecreate && existsSync(venvDir)) {
    log(
      "info",
      "backend",
      "Recreating virtual environment (Python version mismatch)..."
    );
    const { rm } = await import("fs/promises");
    await rm(venvDir, { recursive: true, force: true });
  }

  if (!existsSync(venvPython)) {
    log("info", "backend", "Creating virtual environment...");

    // Find Python 3.11 (canonical backend version)
    const pythonInfo = await findPython311();
    const pythonCmd = pythonInfo.cmd;
    log(
      "info",
      "backend",
      `Using Python: ${pythonCmd} (${pythonInfo.version})`
    );

    await execAsync(`${pythonCmd} -m venv .venv`, { cwd: backendDir });
    log("info", "backend", "Virtual environment created");
  }

  return venvPython;
}

async function installBackendDeps(venvPython, retryCount = 0) {
  const backendDir = join(ROOT_DIR, "backend");

  // Determine which requirements file to use
  const coreFile = join(backendDir, "requirements.core.txt");
  const fallbackFile = join(backendDir, "requirements.txt");
  const ttsFile = join(backendDir, "requirements.extras-tts.txt");

  const reqFile = existsSync(coreFile) ? coreFile : fallbackFile;

  if (!existsSync(reqFile)) {
    throw new Error("No requirements file found");
  }

  log("info", "backend", "Installing backend dependencies...");

  const pipCmd = isWindows()
    ? `"${venvPython}" -m pip install -r "${reqFile}"`
    : `"${venvPython}" -m pip install -r "${reqFile}"`;

  try {
    const { stdout, stderr } = await execAsync(pipCmd, {
      cwd: backendDir,
      maxBuffer: 10 * 1024 * 1024, // 10MB
    });
    await writeFile(join(RUN_DIR, "pip_install.log"), stdout + stderr, "utf8");
    log("info", "backend", "Backend core dependencies installed successfully");

    // Install TTS extras if requested
    if (isWithTTS && existsSync(ttsFile)) {
      log("info", "backend", "Installing TTS extras...");
      const ttsPipCmd = isWindows()
        ? `"${venvPython}" -m pip install -r "${ttsFile}"`
        : `"${venvPython}" -m pip install -r "${ttsFile}"`;

      try {
        const { stdout: ttsStdout, stderr: ttsStderr } = await execAsync(
          ttsPipCmd,
          {
            cwd: backendDir,
            maxBuffer: 10 * 1024 * 1024,
          }
        );
        const existingLog = await readFile(
          join(RUN_DIR, "pip_install.log"),
          "utf8"
        ).catch(() => "");
        await writeFile(
          join(RUN_DIR, "pip_install.log"),
          existingLog +
            "\n\n=== TTS Extras Installation ===\n" +
            ttsStdout +
            ttsStderr,
          "utf8"
        );
        log("info", "backend", "TTS extras installed successfully");
      } catch (ttsErr) {
        const existingLog = await readFile(
          join(RUN_DIR, "pip_install.log"),
          "utf8"
        ).catch(() => "");
        await writeFile(
          join(RUN_DIR, "pip_install.log"),
          existingLog +
            "\n\n=== TTS Extras Installation Failed ===\n" +
            (ttsErr.stdout || "") +
            (ttsErr.stderr || ""),
          "utf8"
        );
        log(
          "error",
          "backend",
          `TTS extras installation failed: ${ttsErr.message}`
        );

        // Check if it's a Python version error
        const ttsErrorOutput = (ttsErr.stdout || "") + (ttsErr.stderr || "");
        if (
          ttsErrorOutput.includes("Requires-Python") ||
          ttsErrorOutput.includes("requires a different python version")
        ) {
          throw new Error(
            `TTS requires Python 3.11 (found incompatible version). The launcher should have auto-fixed this. Check venv Python version.`
          );
        }

        throw new Error(`Failed to install TTS extras: ${ttsErr.message}`);
      }
    }
  } catch (err) {
    const errorOutput = (err.stdout || "") + (err.stderr || "");
    await writeFile(join(RUN_DIR, "pip_install.log"), errorOutput, "utf8");

    // Check if error is due to Python version incompatibility
    const isVersionError =
      errorOutput.includes("Requires-Python") ||
      errorOutput.includes("requires a different python version") ||
      errorOutput.includes("No matching distribution found");

    if (isVersionError && retryCount === 0) {
      log(
        "warning",
        "backend",
        "Python version incompatibility detected, recreating venv with Python 3.11..."
      );

      // Recreate venv with Python 3.11
      await ensureBackendVenv(true);
      const newVenvPython = isWindows()
        ? join(backendDir, ".venv", "Scripts", "python.exe")
        : join(backendDir, ".venv", "bin", "python");

      // Retry installation
      return await installBackendDeps(newVenvPython, 1);
    }

    throw new Error(`Failed to install backend dependencies: ${err.message}`);
  }
}

async function startBackend(port) {
  const backendDir = join(ROOT_DIR, "backend");
  const venvPython = await ensureBackendVenv();

  // Check if dependencies are installed
  try {
    await execAsync(`"${venvPython}" -c "import fastapi, uvicorn"`, {
      cwd: backendDir,
    });
  } catch {
    await installBackendDeps(venvPython);
  }

  // Run import check before starting uvicorn to catch import-time failures
  log("info", "backend", "Running import check...");
  const importCheckScript = join(backendDir, "scripts", "check_imports.py");
  try {
    const { stdout, stderr } = await execAsync(
      `"${venvPython}" "${importCheckScript}"`,
      { cwd: backendDir, maxBuffer: 10 * 1024 * 1024 }
    );
    if (stdout.trim() === "IMPORT_OK") {
      log("info", "backend", "Import check passed");
    } else {
      throw new Error("Import check failed: unexpected output");
    }
  } catch (err) {
    // Extract file:line from traceback if available
    let firstLocalFrame = null;
    const errorOutput = (err.stdout || "") + (err.stderr || "");
    const tracebackMatch = errorOutput.match(/File "([^"]+)", line (\d+),/g);
    if (tracebackMatch && tracebackMatch.length > 0) {
      // Get the first Python file (not stdlib)
      for (const match of tracebackMatch) {
        const fileMatch = match.match(/File "([^"]+)", line (\d+)/);
        if (fileMatch && fileMatch[1].includes("app/")) {
          firstLocalFrame = `${fileMatch[1]}:${fileMatch[2]}`;
          break;
        }
      }
      // If no app/ file found, use the first match
      if (!firstLocalFrame && tracebackMatch[0]) {
        const fileMatch = tracebackMatch[0].match(/File "([^"]+)", line (\d+)/);
        if (fileMatch) {
          firstLocalFrame = `${fileMatch[1]}:${fileMatch[2]}`;
        }
      }
    }

    log("error", "backend", "Import check failed");
    console.log("\n=== Import Check Error ===");
    console.log(errorOutput);
    console.log("\n");

    // Write error root cause
    await writeErrorRootCause(
      "BACKEND_IMPORT_ERROR",
      `Backend import check failed: ${err.message}`,
      [
        "1. Review the traceback above to identify the failing import",
        "2. Check if all dependencies are installed: cd backend && .venv/bin/python -m pip list",
        "3. Verify Python version: .venv/bin/python --version (must be 3.11.x)",
        "4. Try manual import: cd backend && .venv/bin/python -c 'from app.main import app'",
        "5. Check for syntax errors or type annotation issues in the failing module",
      ],
      { message: err.message, stack: errorOutput, firstLocalFrame }
    );

    throw new Error(
      `Backend import check failed. See error above.${
        firstLocalFrame ? ` First error at: ${firstLocalFrame}` : ""
      }`
    );
  }

  log("info", "backend", `Starting backend on port ${port}...`);

  const { createWriteStream } = await import("fs");
  const stdoutStream = createWriteStream(BACKEND_STDOUT_LOG);
  const stderrStream = createWriteStream(BACKEND_STDERR_LOG);

  const backendProcess = spawn(
    venvPython,
    [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      "0.0.0.0",
      "--port",
      String(port),
    ],
    {
      cwd: backendDir,
      stdio: ["ignore", "pipe", "pipe"],
      shell: false,
    }
  );

  // Redirect stdout/stderr to files
  backendProcess.stdout.pipe(stdoutStream);
  backendProcess.stderr.pipe(stderrStream);

  backendPid = backendProcess.pid;
  await writeFile(BACKEND_PID_FILE, String(backendPid), "utf8");

  // Monitor for immediate exit
  let processExited = false;
  let exitCode = null;
  backendProcess.on("exit", (code) => {
    processExited = true;
    exitCode = code;
  });

  // Wait for health check
  const healthUrl = `http://localhost:${port}/api/health`;
  const healthCheckResult = await checkHealth(healthUrl, 60);

  // Check if process exited during health check
  if (processExited) {
    // Read last 120 lines of stderr
    const { readFileSync } = await import("fs");
    let stderrContent = "";
    try {
      if (existsSync(BACKEND_STDERR_LOG)) {
        stderrContent = readFileSync(BACKEND_STDERR_LOG, "utf8");
        const lines = stderrContent.split("\n");
        const lastLines = lines.slice(-120).join("\n");
        log(
          "error",
          "backend",
          `Backend process exited immediately (exit code: ${exitCode})`
        );
        console.log("\n=== Backend stderr (last 120 lines) ===");
        console.log(lastLines);
        console.log("\n");

        // Extract file:line from traceback if this looks like an import error
        let firstLocalFrame = null;
        let category = "BACKEND_RUNTIME_ERROR";
        const isImportError =
          stderrContent.includes("ImportError") ||
          stderrContent.includes("ModuleNotFoundError") ||
          stderrContent.includes("FastAPIError") ||
          stderrContent.includes("Invalid args for response field");

        if (isImportError) {
          category = "BACKEND_IMPORT_ERROR";
          const tracebackMatch = stderrContent.match(
            /File "([^"]+)", line (\d+),/g
          );
          if (tracebackMatch && tracebackMatch.length > 0) {
            // Get the first app/ file
            for (const match of tracebackMatch) {
              const fileMatch = match.match(/File "([^"]+)", line (\d+)/);
              if (fileMatch && fileMatch[1].includes("app/")) {
                firstLocalFrame = `${fileMatch[1]}:${fileMatch[2]}`;
                break;
              }
            }
            // If no app/ file found, use the first match
            if (!firstLocalFrame && tracebackMatch[0]) {
              const fileMatch = tracebackMatch[0].match(
                /File "([^"]+)", line (\d+)/
              );
              if (fileMatch) {
                firstLocalFrame = `${fileMatch[1]}:${fileMatch[2]}`;
              }
            }
          }
        }

        // Write error root cause
        await writeErrorRootCause(
          category,
          `Backend process exited immediately with code ${exitCode}`,
          isImportError
            ? [
                "1. Review the traceback above to identify the failing import or type error",
                "2. Check if all dependencies are installed: cd backend && .venv/bin/python -m pip list",
                "3. Verify Python version: .venv/bin/python --version (must be 3.11.x)",
                "4. Try manual import: cd backend && .venv/bin/python -c 'from app.main import app'",
                "5. Check for syntax errors or type annotation issues in the failing module",
              ]
            : [
                "1. Review the traceback above to identify the runtime error",
                "2. Check backend stderr log: " + BACKEND_STDERR_LOG,
                "3. Verify all services (Redis, database) are accessible",
                "4. Check for missing environment variables or configuration",
              ],
          {
            message: `Backend process exited with code ${exitCode}`,
            stack: lastLines,
            firstLocalFrame,
          }
        );
      }
    } catch (err) {
      log("warning", "backend", `Could not read stderr log: ${err.message}`);
    }

    throw new Error(
      `Backend process exited immediately with code ${exitCode}. Check stderr above.`
    );
  }

  if (healthCheckResult) {
    log(
      "info",
      "backend",
      `Backend started (PID: ${backendPid}, Port: ${port})`
    );
    return backendPid;
  } else {
    // Health check failed - show last 120 lines of stderr
    const { readFileSync } = await import("fs");
    try {
      if (existsSync(BACKEND_STDERR_LOG)) {
        const stderrContent = readFileSync(BACKEND_STDERR_LOG, "utf8");
        const lines = stderrContent.split("\n");
        const lastLines = lines.slice(-120).join("\n");
        log("error", "backend", "Backend health check failed");
        console.log("\n=== Backend stderr (last 120 lines) ===");
        console.log(lastLines);
        console.log("\n");
      }
    } catch (err) {
      log("warning", "backend", `Could not read stderr log: ${err.message}`);
    }

    backendProcess.kill();
    throw new Error("Backend health check failed");
  }
}

// Frontend management
async function ensureFrontendDeps() {
  const frontendDir = join(ROOT_DIR, "frontend");
  const nodeModules = join(frontendDir, "node_modules");

  if (!existsSync(nodeModules)) {
    log("info", "frontend", "Installing frontend dependencies...");

    try {
      const { stdout, stderr } = await execAsync("npm install", {
        cwd: frontendDir,
        maxBuffer: 10 * 1024 * 1024,
      });
      await writeFile(
        join(RUN_DIR, "npm_install.log"),
        stdout + stderr,
        "utf8"
      );
      log("info", "frontend", "Frontend dependencies installed successfully");
    } catch (err) {
      await writeFile(
        join(RUN_DIR, "npm_install.log"),
        err.stdout + err.stderr,
        "utf8"
      );
      throw new Error(
        `Failed to install frontend dependencies: ${err.message}`
      );
    }
  }
}

async function startFrontend(port) {
  const frontendDir = join(ROOT_DIR, "frontend");

  await ensureFrontendDeps();

  log("info", "frontend", `Starting frontend on port ${port}...`);

  const { createWriteStream } = await import("fs");
  const stdoutStream = createWriteStream(FRONTEND_STDOUT_LOG);
  const stderrStream = createWriteStream(FRONTEND_STDERR_LOG);

  const frontendProcess = spawn("npm", ["run", "dev"], {
    cwd: frontendDir,
    env: { ...process.env, PORT: String(port) },
    stdio: ["ignore", "pipe", "pipe"],
    shell: true,
  });

  // Redirect stdout/stderr to files
  frontendProcess.stdout.pipe(stdoutStream);
  frontendProcess.stderr.pipe(stderrStream);

  frontendPid = frontendProcess.pid;
  await writeFile(FRONTEND_PID_FILE, String(frontendPid), "utf8");

  // Wait for health check
  const healthUrl = `http://localhost:${port}`;
  if (await checkHealth(healthUrl, 60)) {
    log(
      "info",
      "frontend",
      `Frontend started (PID: ${frontendPid}, Port: ${port})`
    );
    return frontendPid;
  } else {
    frontendProcess.kill();
    throw new Error("Frontend health check failed");
  }
}

// Error root cause
async function writeErrorRootCause(
  category,
  message,
  fixSteps = [],
  error = null
) {
  // Extract firstLocalFrame from error object if provided, otherwise from stack
  let firstLocalFrame = null;
  if (error && error.firstLocalFrame) {
    firstLocalFrame = error.firstLocalFrame;
  } else if (error && error.stack) {
    const stackLines = error.stack.split("\n");
    // Find first frame that's not in node_modules or internal Node.js
    for (const line of stackLines) {
      if (line.includes("one.mjs") || line.includes("scripts/")) {
        firstLocalFrame = line.trim();
        break;
      }
    }
    // If no local frame found, use first non-empty line
    if (!firstLocalFrame) {
      firstLocalFrame =
        stackLines.find((line) => line.trim().length > 0)?.trim() || null;
    }
  }

  // Read last N lines from stderr logs
  const { readFileSync } = await import("fs");
  const lastStderrLines = 120;
  let backendStderr = null;
  let frontendStderr = null;

  try {
    if (existsSync(BACKEND_STDERR_LOG)) {
      const content = readFileSync(BACKEND_STDERR_LOG, "utf8");
      const lines = content.split("\n");
      backendStderr = lines.slice(-lastStderrLines).join("\n");
    }
  } catch (err) {
    // Ignore read errors
  }

  try {
    if (existsSync(FRONTEND_STDERR_LOG)) {
      const content = readFileSync(FRONTEND_STDERR_LOG, "utf8");
      const lines = content.split("\n");
      frontendStderr = lines.slice(-lastStderrLines).join("\n");
    }
  } catch (err) {
    // Ignore read errors
  }

  const errorInfo = {
    category,
    message,
    timestamp: new Date().toISOString(),
    firstLocalFrame,
    suggestedFix:
      fixSteps.length > 0 ? fixSteps : ["Review logs in " + RUN_DIR],
    lastStderrLines: {
      backend: backendStderr,
      frontend: frontendStderr,
    },
    log_file: RUN_DIR,
  };

  await writeJsonFile(ERROR_ROOT_CAUSE_JSON, errorInfo);
  log("error", "launcher", `ROOT CAUSE: ${category}`);
  log("error", "launcher", message);

  if (firstLocalFrame) {
    log("error", "launcher", `First local frame: ${firstLocalFrame}`);
  }

  if (fixSteps.length > 0) {
    console.log("\nFIX STEPS:");
    fixSteps.forEach((step) => console.log(`  ${step}`));
  }
  console.log(`\nLogs: ${RUN_DIR}\n`);
}

// Diagnose command
async function diagnose() {
  log("info", "launcher", "Running diagnostics...");

  // Find latest run
  let latestRun = null;
  try {
    const latestTimestamp = (await readFile(LATEST_FILE, "utf8")).trim();
    latestRun = join(RUNS_DIR, latestTimestamp);
  } catch {
    // Try to find latest by timestamp
    try {
      const runs = await readdir(RUNS_DIR);
      const dirs = await Promise.all(
        runs.map(async (run) => {
          const path = join(RUNS_DIR, run);
          const stats = await stat(path);
          return { path, mtime: stats.mtime };
        })
      );
      dirs.sort((a, b) => b.mtime - a.mtime);
      if (dirs.length > 0) {
        latestRun = dirs[0].path;
      }
    } catch {}
  }

  if (!latestRun) {
    console.log("No previous run found.");
    return;
  }

  console.log(`\nLast run: ${latestRun}\n`);

  // Read last 120 lines of stderr logs
  const backendStderr = join(latestRun, "backend.stderr.log");
  const frontendStderr = join(latestRun, "frontend.stderr.log");

  try {
    const { readFileSync } = await import("fs");
    if (existsSync(backendStderr)) {
      const content = readFileSync(backendStderr, "utf8");
      const lines = content.split("\n");
      const lastLines = lines.slice(-120).join("\n");
      console.log("=== Backend stderr (last 120 lines) ===");
      console.log(lastLines);
      console.log("\n");
    } else {
      console.log("Backend stderr log not found.\n");
    }

    if (existsSync(frontendStderr)) {
      const content = readFileSync(frontendStderr, "utf8");
      const lines = content.split("\n");
      const lastLines = lines.slice(-120).join("\n");
      console.log("=== Frontend stderr (last 120 lines) ===");
      console.log(lastLines);
      console.log("\n");
    } else {
      console.log("Frontend stderr log not found.\n");
    }
  } catch (err) {
    log("warning", "launcher", `Could not read logs: ${err.message}`);
  }

  // Read root cause if present
  const rootCauseFile = join(latestRun, "error_root_cause.json");
  if (existsSync(rootCauseFile)) {
    try {
      const rootCause = JSON.parse(await readFile(rootCauseFile, "utf8"));
      console.log("=== Root Cause ===");
      console.log(`Category: ${rootCause.category}`);
      console.log(`Message: ${rootCause.message}`);
      if (rootCause.fix_steps) {
        console.log("\nFix Steps:");
        rootCause.fix_steps.forEach((step) => console.log(`  ${step}`));
      }
      console.log("\n");
    } catch (err) {
      log("warning", "launcher", `Could not parse root cause: ${err.message}`);
    }
  }
}

// Stop command
async function stopServices() {
  log("info", "launcher", "Stopping services...");

  // Stop backend
  if (existsSync(BACKEND_PID_FILE)) {
    try {
      const pid = parseInt(await readFile(BACKEND_PID_FILE, "utf8"), 10);
      if (pid) {
        if (isWindows()) {
          await execAsync(`taskkill /F /PID ${pid}`);
        } else {
          await execAsync(`kill ${pid}`);
        }
        log("info", "backend", `Backend stopped (PID: ${pid})`);
      }
    } catch (err) {
      log("warning", "backend", `Could not stop backend: ${err.message}`);
    }
    const { unlink } = await import("fs/promises");
    await unlink(BACKEND_PID_FILE).catch(() => {});
  }

  // Stop frontend
  if (existsSync(FRONTEND_PID_FILE)) {
    try {
      const pid = parseInt(await readFile(FRONTEND_PID_FILE, "utf8"), 10);
      if (pid) {
        if (isWindows()) {
          await execAsync(`taskkill /F /PID ${pid}`);
        } else {
          await execAsync(`kill ${pid}`);
        }
        log("info", "frontend", `Frontend stopped (PID: ${pid})`);
      }
    } catch (err) {
      log("warning", "frontend", `Could not stop frontend: ${err.message}`);
    }
    const { unlink } = await import("fs/promises");
    await unlink(FRONTEND_PID_FILE).catch(() => {});
  }

  log("info", "launcher", "Services stopped");
}

// Main startup function
async function start() {
  try {
    // Setup directories
    await ensureDir(RUN_DIR);
    await ensureDir(AINFLUENCER_DIR);
    await writeFile(LATEST_FILE, timestamp, "utf8");

    log("info", "launcher", "Starting AInfluencer Launcher");

    // Run doctor checks
    await runDoctor();

    // Check/create .env file
    const envExample = join(ROOT_DIR, ".env.example");
    const envFile = join(ROOT_DIR, ".env");
    if (existsSync(envExample) && !existsSync(envFile)) {
      const { copyFileSync } = await import("fs");
      copyFileSync(envExample, envFile);
      log("info", "launcher", "Created .env file from .env.example");
    } else if (!existsSync(envExample)) {
      log(
        "warning",
        "launcher",
        ".env.example not found, skipping .env creation"
      );
    }

    // Port management
    const backendPorts = [8000, 8001, 8002];
    const frontendPorts = [3000, 3001, 3002];

    const backendPortInfo = await getAvailablePort(backendPorts, "backend");
    const frontendPortInfo = await getAvailablePort(frontendPorts, "frontend");

    backendPort = backendPortInfo.port;
    frontendPort = frontendPortInfo.port;

    await writeJsonFile(PORTS_FILE, {
      backend: backendPort,
      frontend: frontendPort,
      backend_reused: backendPortInfo.reused,
      frontend_reused: frontendPortInfo.reused,
    });

    // Start backend if not reused
    if (!backendPortInfo.reused) {
      await startBackend(backendPort);
    } else {
      log("info", "launcher", "Backend already running, skipping start");
      backendPid = backendPortInfo.pid;
    }

    // Start frontend if not reused
    if (!frontendPortInfo.reused) {
      await startFrontend(frontendPort);
    } else {
      log("info", "launcher", "Frontend already running, skipping start");
      frontendPid = frontendPortInfo.pid;
    }

    // Write run summary
    await writeJsonFile(RUN_SUMMARY_JSON, {
      status: "SUCCESS",
      timestamp: new Date().toISOString(),
      backend: {
        port: backendPort,
        pid: backendPid,
        reused: backendPortInfo.reused,
      },
      frontend: {
        port: frontendPort,
        pid: frontendPid,
        reused: frontendPortInfo.reused,
      },
      logs: RUN_DIR,
    });

    // Open browser
    log("info", "launcher", "Opening dashboard in browser...");
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const url = `http://localhost:${frontendPort}`;
    if (isMac()) {
      await execAsync(`open "${url}"`);
    } else if (isWindows()) {
      await execAsync(`start "" "${url}"`);
    } else {
      await execAsync(`xdg-open "${url}"`);
    }

    log("info", "launcher", "All services started successfully");
    console.log("\n✓ SUCCESS: AInfluencer is running!");
    console.log(`  Dashboard: http://localhost:${frontendPort}`);
    console.log(`  Backend API: http://localhost:${backendPort}`);
    console.log(`  Logs: ${RUN_DIR}`);
    console.log("\nPress Ctrl+C to stop all services...\n");

    // Wait for interrupt
    process.on("SIGINT", async () => {
      console.log("\n");
      await stopServices();
      process.exit(0);
    });

    process.on("SIGTERM", async () => {
      await stopServices();
      process.exit(0);
    });

    // Keep process alive
    await new Promise(() => {});
  } catch (err) {
    log("error", "launcher", `Startup failed: ${err.message}`);

    // Write error root cause
    let category = "UNKNOWN_ERROR";
    let fixSteps = [];

    if (
      err.message.includes("Python") &&
      (err.message.includes("not found") ||
        err.message.includes("wrong version"))
    ) {
      category = "ENV_MISSING";
      if (isMac()) {
        fixSteps = [
          "1. Install Python 3.11: brew install python@3.11",
          "2. Verify: python3.11 --version",
          "3. Re-run launcher",
          "4. Or set override: AINFLUENCER_PYTHON=/path/to/python3.11 node scripts/one.mjs",
        ];
      } else {
        fixSteps = [
          "1. Install Python 3.11 from python.org",
          "2. Ensure Python is in PATH",
          "3. Re-run launcher",
        ];
      }
    } else if (err.message.includes("Node.js not found")) {
      category = "ENV_MISSING";
      fixSteps = [
        "1. Install Node.js LTS from nodejs.org",
        "2. Re-run launcher",
      ];
    } else if (
      err.message.includes("backend dependencies") ||
      err.message.includes("TTS extras")
    ) {
      category = "PIP_INSTALL_FAILED";
      const pythonCheck = isMac() ? "python3.11 --version" : "python --version";
      fixSteps = [
        `1. Check Python version: ${pythonCheck} (must be 3.11.x)`,
        "2. Review log: " + join(RUN_DIR, "pip_install.log"),
        "3. If Python version error, venv was recreated automatically",
        "4. Try manual install: cd backend && .venv/bin/python -m pip install -r requirements.core.txt",
        isWithTTS
          ? "5. For TTS: cd backend && .venv/bin/python -m pip install -r requirements.extras-tts.txt"
          : "",
      ].filter(Boolean);
    } else if (err.message.includes("frontend dependencies")) {
      category = "NPM_INSTALL_FAILED";
      fixSteps = [
        "1. Check Node.js: node --version",
        "2. Clear npm cache: npm cache clean --force",
        "3. Review log: " + join(RUN_DIR, "npm_install.log"),
        "4. Try manual install: cd frontend && npm install",
      ];
    } else if (
      err.message.includes("Backend import check failed") ||
      err.message.includes("Import check failed")
    ) {
      category = "BACKEND_IMPORT_ERROR";
      fixSteps = [
        "1. Review the traceback in the output above",
        "2. Check if all dependencies are installed: cd backend && .venv/bin/python -m pip list",
        "3. Verify Python version: .venv/bin/python --version (must be 3.11.x)",
        "4. Try manual import: cd backend && .venv/bin/python -c 'from app.main import app'",
        "5. Check for syntax errors or type annotation issues in the failing module",
      ];
    } else if (err.message.includes("Backend health check")) {
      category = "BACKEND_HEALTHCHECK_TIMEOUT";
      fixSteps = [
        "1. Check backend stderr log: " + BACKEND_STDERR_LOG,
        "2. Verify backend is listening on port " + backendPort,
        "3. Check for import errors or missing dependencies",
      ];
    } else if (err.message.includes("Frontend health check")) {
      category = "FRONTEND_HEALTHCHECK_TIMEOUT";
      fixSteps = [
        "1. Check frontend stderr log: " + FRONTEND_STDERR_LOG,
        "2. Verify frontend is listening on port " + frontendPort,
        "3. Check for build errors or missing dependencies",
      ];
    }

    await writeErrorRootCause(category, err.message, fixSteps, err);

    await writeJsonFile(RUN_SUMMARY_JSON, {
      status: "FAILED",
      timestamp: new Date().toISOString(),
      error: err.message,
      logs: RUN_DIR,
    });

    process.exit(1);
  }
}

// Doctor command - runs preflight checks
async function runDoctorCommand() {
  log("info", "launcher", "Running doctor checks...");

  const doctorScript = isWindows()
    ? join(ROOT_DIR, "scripts", "doctor.ps1")
    : join(ROOT_DIR, "scripts", "doctor.sh");

  if (!existsSync(doctorScript)) {
    log(
      "warning",
      "launcher",
      "Doctor script not found, running inline checks"
    );
    try {
      await runInlineChecks();
      console.log("\n✓ All checks passed!");
      process.exit(0);
    } catch (err) {
      console.log(`\n✗ Checks failed: ${err.message}`);
      process.exit(1);
    }
    return;
  }

  try {
    const cmd = isWindows()
      ? `powershell.exe -ExecutionPolicy Bypass -File "${doctorScript}"`
      : `bash "${doctorScript}"`;

    const { stdout, stderr } = await execAsync(cmd, { cwd: ROOT_DIR });
    console.log(stdout);
    if (stderr) {
      console.error(stderr);
    }
    process.exit(0);
  } catch (err) {
    console.error(`Doctor checks failed: ${err.message}`);
    if (err.stdout) console.log(err.stdout);
    if (err.stderr) console.error(err.stderr);
    process.exit(1);
  }
}

// Main entry point
(async () => {
  if (isDoctor) {
    await runDoctorCommand();
  } else if (isDiagnose) {
    await diagnose();
  } else if (isStop) {
    await stopServices();
  } else {
    await start();
  }
})();
