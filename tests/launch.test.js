/**
 * Tests for launch() in src/core/health.js.
 *
 * On Windows, PowerShell's Start-Process is the *primary* launch mechanism —
 * Node's detached child_process.spawn() can throw EPERM synchronously for
 * both the WindowsApps (MSIX) binary and the locally-copied binary, which
 * would otherwise crash launch() before any fallback logic runs. Every deps
 * object below makes `spawn` throw if called at all, as a regression guard:
 * these tests fail loudly if Windows launches ever start using it again.
 *
 * Covers: MSIX WindowsApps attempt, local-copy fallback when the WindowsApps
 * attempt fails or CDP never binds, copy reuse, the real PowerShell command
 * construction, and classic (non-MSIX) installs.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { launch } from '../src/core/health.js';

const MSIX_EXE = 'C:\\Program Files\\WindowsApps\\TradingView.Desktop_3.1.0.7818_x64__n534cwy3pjxzj\\TradingView.exe';
const LOCAL_COPY_EXE = `${process.env.LOCALAPPDATA || ''}\\tradingview-mcp\\TradingView.Desktop_3.1.0.7818_x64__n534cwy3pjxzj\\TradingView.exe`;
const CDP_VERSION = JSON.stringify({ Browser: 'Chrome/140', 'User-Agent': 'TVDesktop/3.1.0' });

// spawn() must never be invoked for a win32 launch — see file header.
const spawnMustNotBeCalled = () => { throw new Error('spawn() must not be used on win32 — use startWindowsProcess'); };

// ── Mock helpers ─────────────────────────────────────────────────────────

/**
 * Build a _deps bundle simulating a win32 MSIX environment.
 * @param {object} opts
 *   launchFailures — startWindowsProcess exe paths (substring) that throw, simulating
 *                    PowerShell/Start-Process failing for that binary (e.g. real-world EPERM)
 *   cdpBindsFor    — exe paths (substring) after which probeCdp starts succeeding
 *   copyExists     — local copy already present
 */
function msixDeps({ launchFailures = [], cdpBindsFor = [], copyExists = false } = {}) {
  const state = { psLaunches: [], copies: [], removed: [], killed: 0, cdpUp: false };
  const deps = {
    existsSync: (p) => {
      if (p === MSIX_EXE) return true;
      if (p.includes('tradingview-mcp')) return copyExists || state.copies.length > 0;
      return false;
    },
    execSync: (cmd) => {
      if (cmd.includes('Get-AppxPackage')) {
        return 'C:\\Program Files\\WindowsApps\\TradingView.Desktop_3.1.0.7818_x64__n534cwy3pjxzj\n';
      }
      if (cmd.includes('taskkill')) { state.killed++; return ''; }
      throw new Error(`unexpected execSync: ${cmd}`);
    },
    spawn: spawnMustNotBeCalled,
    startWindowsProcess: (exe, args) => {
      state.psLaunches.push({ exe, args });
      if (launchFailures.some((s) => exe.includes(s))) throw new Error('spawn EPERM');
      if (cdpBindsFor.some((s) => exe.includes(s))) state.cdpUp = true;
      return 54321;
    },
    cpSync: (src, dst) => { state.copies.push({ src, dst }); },
    rmSync: (p) => { state.removed.push(p); },
    readdirSync: () => ['TradingView.Desktop_3.0.0.7652_x64__n534cwy3pjxzj'],
    delay: async () => {},
    probeCdp: async () => (state.cdpUp ? CDP_VERSION : null),
  };
  return { deps, state };
}

// launch() only takes the MSIX/win32 code paths tested here on win32; skip elsewhere.
const onWindows = process.platform === 'win32';

describe('launch() — MSIX WindowsApps handling', { skip: !onWindows }, () => {
  it('direct WindowsApps launch that binds CDP does not copy', async () => {
    const { deps, state } = msixDeps({ cdpBindsFor: ['WindowsApps'] });
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.binary, MSIX_EXE);
    assert.equal(result.pid, 54321);
    assert.equal(result.msix_local_copy, undefined);
    assert.equal(state.copies.length, 0);
    assert.equal(result.cdp_url, 'http://127.0.0.1:9222');
  });

  it('PowerShell failure on the WindowsApps attempt falls back to the local copy (regression: must not crash launch())', async () => {
    // Simulates the real-world bug: Start-Process throws for the WindowsApps
    // binary. launch() must catch this and fall back, not reject immediately.
    const { deps, state } = msixDeps({ launchFailures: ['WindowsApps'], cdpBindsFor: ['tradingview-mcp'] });
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.msix_local_copy, true);
    assert.equal(result.binary, LOCAL_COPY_EXE);
    assert.equal(result.pid, 54321);
    assert.equal(state.copies.length, 1);
    assert.match(state.copies[0].src, /WindowsApps/);
    // stale cached version of another release is cleaned up first
    assert.equal(state.removed.length, 1);
    assert.match(state.removed[0], /3\.0\.0\.7652/);
    // the failed direct attempt is killed before relaunching from the copy
    assert.ok(state.killed >= 2);
    // both attempts go through PowerShell Start-Process, never spawn()
    assert.equal(state.psLaunches.length, 2);
    assert.match(state.psLaunches[0].exe, /WindowsApps/);
    assert.match(state.psLaunches[1].exe, /tradingview-mcp/);
    assert.deepEqual(state.psLaunches[1].args, ['--remote-debugging-port=9222']);
  });

  it('CDP never binding on the WindowsApps attempt falls back to the local copy', async () => {
    const { deps, state } = msixDeps({ cdpBindsFor: ['tradingview-mcp'] });
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.msix_local_copy, true);
    assert.equal(state.psLaunches.length, 2);
    assert.match(state.psLaunches[0].exe, /WindowsApps/);
    assert.match(state.psLaunches[1].exe, /tradingview-mcp/);
  });

  it('reuses an existing local copy without re-copying', async () => {
    const { deps, state } = msixDeps({ launchFailures: ['WindowsApps'], cdpBindsFor: ['tradingview-mcp'], copyExists: true });
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.msix_local_copy, true);
    assert.equal(state.copies.length, 0);
    assert.equal(state.psLaunches.length, 2);
  });

  it('returns cdp_ready:false warning when nothing binds', async () => {
    const { deps } = msixDeps({});
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.cdp_ready, false);
    assert.equal(result.msix_local_copy, true);
    assert.ok(result.warning);
  });
});

describe('launch() — PowerShell Start-Process command (real implementation)', { skip: !onWindows }, () => {
  // Exercises the default startWindowsProcess implementation (not mocked away)
  // via a classic (non-MSIX) install, so exactly one PowerShell launch happens.
  // Intercepts the `powershell -EncodedCommand ...` call at the execSync layer,
  // decodes the payload, and asserts on the actual script produced.
  const classicExe = `${process.env.LOCALAPPDATA}\\TradingView\\TradingView.exe`;

  function psRealDeps({ psOutput = '54321\n' } = {}) {
    const state = { killed: 0, psCommands: [], lastScript: null };
    const deps = {
      existsSync: (p) => p === classicExe,
      execSync: (cmd) => {
        if (cmd.includes('taskkill')) { state.killed++; return ''; }
        if (cmd.includes('-EncodedCommand')) {
          state.psCommands.push(cmd);
          const encoded = cmd.split('-EncodedCommand ')[1].trim();
          state.lastScript = Buffer.from(encoded, 'base64').toString('utf16le');
          return psOutput;
        }
        throw new Error(`unexpected execSync: ${cmd}`);
      },
      spawn: spawnMustNotBeCalled,
      cpSync: () => { throw new Error('should not copy'); },
      rmSync: () => {},
      readdirSync: () => [],
      delay: async () => {},
      probeCdp: async () => CDP_VERSION,
    };
    return { deps, state };
  }

  it('builds a Start-Process command encoding the exe path and CDP port argument', async () => {
    const { deps, state } = psRealDeps();
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.binary, classicExe);
    assert.equal(result.pid, 54321);
    assert.equal(state.psCommands.length, 1);
    assert.match(state.psCommands[0], /^powershell -NoProfile -NonInteractive -EncodedCommand /);
    assert.match(state.lastScript, /Start-Process -FilePath '[^']*\\TradingView\\TradingView\.exe' -ArgumentList '--remote-debugging-port=9222' -PassThru/);
    assert.match(state.lastScript, /Write-Output \$p\.Id/);
  });

  it('throws a clear error when PowerShell does not return a numeric PID', async () => {
    const { deps } = psRealDeps({ psOutput: 'Access is denied.\n' });
    await assert.rejects(() => launch({ _deps: deps }), /PowerShell Start-Process did not return a PID/);
  });
});

describe('launch() — classic install path', { skip: !onWindows }, () => {
  it('launches classic LOCALAPPDATA install via PowerShell, without MSIX logic', async () => {
    const classicExe = `${process.env.LOCALAPPDATA}\\TradingView\\TradingView.exe`;
    const state = { psLaunches: [] };
    const deps = {
      existsSync: (p) => p === classicExe,
      execSync: (cmd) => { if (cmd.includes('taskkill')) return ''; throw new Error(`unexpected: ${cmd}`); },
      spawn: spawnMustNotBeCalled,
      startWindowsProcess: (exe, args) => { state.psLaunches.push({ exe, args }); return 54321; },
      cpSync: () => { throw new Error('should not copy'); },
      rmSync: () => {},
      readdirSync: () => [],
      delay: async () => {},
      probeCdp: async () => CDP_VERSION,
    };
    const result = await launch({ _deps: deps });
    assert.equal(result.success, true);
    assert.equal(result.binary, classicExe);
    assert.equal(result.pid, 54321);
    assert.equal(result.msix_local_copy, undefined);
    assert.deepEqual(state.psLaunches, [{ exe: classicExe, args: ['--remote-debugging-port=9222'] }]);
  });

  it('throws immediately when the PowerShell launch fails for a classic install (no fallback exists)', async () => {
    const classicExe = `${process.env.LOCALAPPDATA}\\TradingView\\TradingView.exe`;
    const deps = {
      existsSync: (p) => p === classicExe,
      execSync: (cmd) => { if (cmd.includes('taskkill')) return ''; throw new Error(`unexpected: ${cmd}`); },
      spawn: spawnMustNotBeCalled,
      startWindowsProcess: () => { throw new Error('spawn EPERM'); },
      cpSync: () => { throw new Error('should not copy'); },
      rmSync: () => {},
      readdirSync: () => [],
      delay: async () => {},
      probeCdp: async () => null,
    };
    await assert.rejects(() => launch({ _deps: deps }), /Failed to launch TradingView via PowerShell Start-Process: spawn EPERM/);
  });

  it('throws a helpful error when TradingView is not found', async () => {
    const deps = {
      existsSync: () => false,
      execSync: () => { throw new Error('not found'); },
      spawn: spawnMustNotBeCalled,
      startWindowsProcess: spawnMustNotBeCalled,
      cpSync: () => {}, rmSync: () => {}, readdirSync: () => [],
      delay: async () => {}, probeCdp: async () => null,
    };
    await assert.rejects(() => launch({ _deps: deps }), /TradingView not found/);
  });
});
