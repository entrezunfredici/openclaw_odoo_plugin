import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";
import { getPluginConfig } from "./config.js";
import { runPythonAction } from "./pythonBridge.js";

function toToolText(result: unknown): string {
    return JSON.stringify(result, null, 2);
}

export default definePluginEntry({
    id: "odoo-plugin",
    name: "Odoo Plugin",
    description: "Safe Odoo connector for OpenClaw",

    register(api: any) {
        api.registerTool({
            name: "odoo_list_tasks",
            description: "Bounded read: list tasks from a specific Odoo project",
            parameters: Type.Object({
                project_id: Type.Number(),
                limit: Type.Optional(Type.Number()),
            }),
            async execute(_id: string, params: { project_id: number; limit?: number }) {
                const config = getPluginConfig(api);
                const result = await runPythonAction("list_tasks", { ...params, config });

                return {
                    content: [{ type: "text", text: toToolText(result) }],
                };
            },
        });

        api.registerTool(
            {
                name: "odoo_create_task",
                description:
                    "Bounded write: create a project task after validation, policy checks, and logging",
                parameters: Type.Object({
                    project_id: Type.Number(),
                    name: Type.String(),
                    description: Type.Optional(Type.String()),
                    confirmed: Type.Optional(Type.Boolean()),
                }),
                async execute(_id: string, params: { project_id: number; name: string; description?: string; confirmed?: boolean }) {
                    const config = getPluginConfig(api);
                    const result = await runPythonAction("create_task", { ...params, config });

                    return {
                        content: [{ type: "text", text: toToolText(result) }],
                    };
                },
            },
            { optional: true },
        );
    },
});
