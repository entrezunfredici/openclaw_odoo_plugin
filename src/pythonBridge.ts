import { spawn } from "node:child_process";

export function runPythonAction(action: string, payload: object): Promise<any> {
    return new Promise((resolve, reject) => {
        const child = spawn("python3", ["python/odoo_connector/cli.py"], {
            stdio: ["pipe", "pipe", "pipe"]
        });

        let stdout = "";
        let stderr = "";

        child.stdout.on("data", (data) => {
            stdout += data.toString();
        });

        child.stderr.on("data", (data) => {
            stderr += data.toString();
        });

        child.on("close", (code) => {
            if (code !== 0) {
                reject(new Error(stderr || `Python process exited with code ${code}`));
                return;
            }

            try {
                resolve(JSON.parse(stdout));
            } catch (e) {
                reject(new Error(`Invalid JSON from Python: ${stdout}`));
            }
        });

        child.stdin.write(JSON.stringify({ action, payload }));
        child.stdin.end();
    });
}
