#!/usr/bin/env node
/**
 * Pipeline Phase 1 Smoke Test
 * 
 * Tests the basic pipeline functionality:
 * - List presets
 * - Generate image with a preset
 * - Poll job status
 * - Verify artifact exists
 * 
 * Usage:
 *   node scripts/smoke/pipeline_phase1.mjs [--backend-url http://localhost:8000]
 */

import { spawn } from "child_process";
import { setTimeout } from "timers/promises";

const BACKEND_URL = process.env.BACKEND_URL || process.argv.includes("--backend-url")
  ? process.argv[process.argv.indexOf("--backend-url") + 1]
  : "http://localhost:8000";

const API_BASE = `${BACKEND_URL}/api`;

let testsPassed = 0;
let testsFailed = 0;

function log(message) {
  console.log(`[SMOKE] ${message}`);
}

function error(message) {
  console.error(`[SMOKE ERROR] ${message}`);
}

async function httpRequest(method, path, body = null) {
  const url = `${API_BASE}${path}`;
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);
    const data = await response.json();
    return { status: response.status, data };
  } catch (e) {
    throw new Error(`HTTP request failed: ${e.message}`);
  }
}

async function testListPresets() {
  log("Test 1: List presets");
  try {
    const { status, data } = await httpRequest("GET", "/presets");
    if (status !== 200) {
      throw new Error(`Expected 200, got ${status}`);
    }
    if (!data.ok) {
      throw new Error(`Response not ok: ${JSON.stringify(data)}`);
    }
    if (!Array.isArray(data.presets)) {
      throw new Error("Presets is not an array");
    }
    if (data.presets.length === 0) {
      throw new Error("No presets found");
    }
    log(`✓ Found ${data.presets.length} presets`);
    testsPassed++;
    return data.presets[0].id; // Return first preset ID
  } catch (e) {
    error(`Failed: ${e.message}`);
    testsFailed++;
    return null;
  }
}

async function testGenerateImage(presetId) {
  log(`Test 2: Generate image with preset ${presetId}`);
  try {
    const { status, data } = await httpRequest("POST", "/generate/image", {
      preset_id: presetId,
      prompt: "A simple test image, a red circle on white background",
      quality_level: "low",
    });

    if (status !== 200) {
      throw new Error(`Expected 200, got ${status}: ${JSON.stringify(data)}`);
    }

    if (!data.job_id) {
      throw new Error("Response missing job_id");
    }

    if (!["queued", "running", "completed"].includes(data.status)) {
      throw new Error(`Unexpected status: ${data.status}`);
    }

    log(`✓ Job created: ${data.job_id} (status: ${data.status})`);
    testsPassed++;
    return data.job_id;
  } catch (e) {
    error(`Failed: ${e.message}`);
    testsFailed++;
    return null;
  }
}

async function testPollJobStatus(jobId, maxAttempts = 30) {
  log(`Test 3: Poll job status for ${jobId}`);
  try {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const { status, data } = await httpRequest("GET", `/jobs/${jobId}`);

      if (status !== 200) {
        throw new Error(`Expected 200, got ${status}: ${JSON.stringify(data)}`);
      }

      if (data.status === "completed") {
        if (!data.output_url) {
          throw new Error("Job completed but no output_url");
        }
        log(`✓ Job completed: ${data.output_url}`);
        testsPassed++;
        return data.output_url;
      }

      if (data.status === "failed") {
        throw new Error(`Job failed: ${data.error || "Unknown error"}`);
      }

      // Still running or queued
      if (attempt < maxAttempts - 1) {
        await setTimeout(2000); // Wait 2 seconds before next poll
      }
    }

    throw new Error(`Job did not complete within ${maxAttempts * 2} seconds`);
  } catch (e) {
    error(`Failed: ${e.message}`);
    testsFailed++;
    return null;
  }
}

async function testGetArtifacts(jobId) {
  log(`Test 4: Get artifacts for job ${jobId}`);
  try {
    const { status, data } = await httpRequest("GET", `/jobs/${jobId}/artifacts`);

    if (status !== 200) {
      throw new Error(`Expected 200, got ${status}: ${JSON.stringify(data)}`);
    }

    if (!data.ok) {
      throw new Error(`Response not ok: ${JSON.stringify(data)}`);
    }

    if (!Array.isArray(data.artifacts)) {
      throw new Error("Artifacts is not an array");
    }

    if (data.artifacts.length === 0) {
      throw new Error("No artifacts found");
    }

    log(`✓ Found ${data.artifacts.length} artifact(s)`);
    testsPassed++;
    return true;
  } catch (e) {
    error(`Failed: ${e.message}`);
    testsFailed++;
    return false;
  }
}

async function checkBackendHealth() {
  log("Checking backend health...");
  try {
    const { status } = await httpRequest("GET", "/health");
    if (status === 200) {
      log("✓ Backend is healthy");
      return true;
    }
    throw new Error(`Backend health check failed: ${status}`);
  } catch (e) {
    error(`Backend not reachable at ${BACKEND_URL}: ${e.message}`);
    error("Make sure the backend is running: node scripts/one.mjs");
    return false;
  }
}

async function main() {
  log("Starting Pipeline Phase 1 Smoke Test");
  log(`Backend URL: ${BACKEND_URL}`);

  // Check backend health
  const healthy = await checkBackendHealth();
  if (!healthy) {
    process.exit(1);
  }

  // Run tests
  const presetId = await testListPresets();
  if (!presetId) {
    error("Cannot continue without a preset");
    process.exit(1);
  }

  const jobId = await testGenerateImage(presetId);
  if (!jobId) {
    error("Cannot continue without a job");
    process.exit(1);
  }

  const outputUrl = await testPollJobStatus(jobId);
  if (!outputUrl) {
    error("Job did not complete successfully");
    process.exit(1);
  }

  await testGetArtifacts(jobId);

  // Summary
  log("\n=== Test Summary ===");
  log(`Passed: ${testsPassed}`);
  log(`Failed: ${testsFailed}`);

  if (testsFailed === 0) {
    log("\n✓ All tests passed!");
    process.exit(0);
  } else {
    error(`\n✗ ${testsFailed} test(s) failed`);
    process.exit(1);
  }
}

main().catch((e) => {
  error(`Unexpected error: ${e.message}`);
  console.error(e);
  process.exit(1);
});
