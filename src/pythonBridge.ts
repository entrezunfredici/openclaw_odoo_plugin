import { dirname, resolve } from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const pluginRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

export interface BridgeRequest {
    action: string;
    model?: string;
    payload?: Record<string, unknown>;
    config: Record<string, unknown>;
}

export function runPythonAction(request: BridgeRequest): Promise<unknown> {
    return new Promise((resolvePromise, rejectPromise) => {
        const child = spawn("python3", ["-m", "python.odoo_connector.cli"], {
            cwd: pluginRoot,
            stdio: ["pipe", "pipe", "pipe"],
        });

        let stdout = "";
        let stderr = "";

        child.stdout.on("data", (data: Buffer) => { stdout += data.toString(); });
        child.stderr.on("data", (data: Buffer) => { stderr += data.toString(); });

        child.on("close", (code: number | null) => {
            if (code !== 0) {
                rejectPromise(new Error(stderr || `Python process exited with code ${code}`));
                return;
            }
            try {
                resolvePromise(JSON.parse(stdout));
            } catch {
                rejectPromise(new Error(`Invalid JSON from Python: ${stdout}`));
            }
        });

        child.stdin.write(JSON.stringify(request));
        child.stdin.end();
    });
}
