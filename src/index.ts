/**
 * Odoo Plugin for OpenClaw
 *
 * Exposes bounded, policy-enforced Odoo tools to the AI agent.
 * All field-level access is governed by the permission rules configured
 * by the user in the OpenClaw interface — the agent cannot bypass them.
 *
 * Tools registered:
 *   Meta / config UI helpers:
 *     odoo_list_models        — list available Odoo models (for selector)
 *     odoo_list_fields        — list fields of a model (for selector)
 *
 *   Generic CRUD (policy-enforced):
 *     odoo_read               — read records from any allowed model
 *     odoo_create             — create a record in any allowed model
 *     odoo_write              — update records in any allowed model
 *     odoo_delete             — delete records in any allowed model
 *
 *   Audit:
 *     odoo_rollback           — attempt rollback via snapshot
 */

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
    description: "Policy-enforced Odoo connector — all access governed by user-defined permission rules",

    register(api: any) {

        // ----------------------------------------------------------------
        // META TOOLS — used by the OpenClaw UI to populate selectors
        // ----------------------------------------------------------------

        api.registerTool({
            name: "odoo_list_models",
            description:
                "List all Odoo models available on the active connection. " +
                "Use this to discover which models exist before configuring permission rules.",
            parameters: Type.Object({}),
            async execute(_id: string, _params: Record<string, never>) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_list_models",
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });

        api.registerTool({
            name: "odoo_list_fields",
            description:
                "List all fields of a given Odoo model, with their type, label, and metadata. " +
                "Use this to discover which fields to include in permission rules.",
            parameters: Type.Object({
                model: Type.String({ description: "Odoo technical model name, e.g. 'project.task'" }),
            }),
            async execute(_id: string, params: { model: string }) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_list_fields",
                    model: params.model,
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });

        // ----------------------------------------------------------------
        // READ — filtered to fields allowed by permission rules
        // ----------------------------------------------------------------

        api.registerTool({
            name: "odoo_read",
            description:
                "Read records from an Odoo model. Only fields explicitly allowed by the active " +
                "access profile's permission rules will be returned. " +
                "Use odoo_list_models / odoo_list_fields to discover available models and fields.",
            parameters: Type.Object({
                model: Type.String({ description: "Odoo model name, e.g. 'project.task'" }),
                fields: Type.Optional(
                    Type.Array(Type.String(), { description: "Fields to read. Defaults to ['id','name']." })
                ),
                domain: Type.Optional(
                    Type.Array(Type.Any(), { description: "Odoo domain filter, e.g. [['project_id','=',1]]" })
                ),
                limit: Type.Optional(Type.Number({ description: "Max records to return" })),
            }),
            async execute(_id: string, params: { model: string; fields?: string[]; domain?: unknown[]; limit?: number }) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_read",
                    model: params.model,
                    payload: { fields: params.fields, domain: params.domain, limit: params.limit },
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });

        // ----------------------------------------------------------------
        // CREATE — field-level policy + confirmation + snapshot
        // ----------------------------------------------------------------

        api.registerTool(
            {
                name: "odoo_create",
                description:
                    "Create a record in an Odoo model. Only fields allowed by permission rules " +
                    "will be written. If confirmation is required by policy, set confirmed=true " +
                    "after the user acknowledges. Optionally use a template_id.",
                parameters: Type.Object({
                    model: Type.String({ description: "Odoo model name" }),
                    values: Type.Optional(
                        Type.Record(Type.String(), Type.Any(), {
                            description: "Field values to set on the new record",
                        })
                    ),
                    template_id: Type.Optional(Type.String({ description: "Template id to use" })),
                    variables: Type.Optional(
                        Type.Record(Type.String(), Type.Any(), { description: "Template variables" })
                    ),
                    confirmed: Type.Optional(
                        Type.Boolean({ description: "Set true to confirm the operation when required by policy" })
                    ),
                }),
                async execute(
                    _id: string,
                    params: {
                        model: string;
                        values?: Record<string, unknown>;
                        template_id?: string;
                        variables?: Record<string, unknown>;
                        confirmed?: boolean;
                    }
                ) {
                    const config = getPluginConfig(api);
                    const result = await runPythonAction({
                        action: "odoo_create",
                        model: params.model,
                        payload: {
                            values: params.values,
                            template_id: params.template_id,
                            variables: params.variables,
                            confirmed: params.confirmed,
                        },
                        config,
                    });
                    return { content: [{ type: "text", text: toToolText(result) }] };
                },
            },
            { optional: true },
        );

        // ----------------------------------------------------------------
        // WRITE — field-level policy + snapshot before write
        // ----------------------------------------------------------------

        api.registerTool(
            {
                name: "odoo_write",
                description:
                    "Update existing records in an Odoo model. Only fields allowed by permission " +
                    "rules will be written. The previous state is snapshotted for potential rollback.",
                parameters: Type.Object({
                    model: Type.String({ description: "Odoo model name" }),
                    ids: Type.Array(Type.Number(), { description: "Record ids to update" }),
                    values: Type.Record(Type.String(), Type.Any(), { description: "Fields to update" }),
                    confirmed: Type.Optional(Type.Boolean()),
                }),
                async execute(
                    _id: string,
                    params: { model: string; ids: number[]; values: Record<string, unknown>; confirmed?: boolean }
                ) {
                    const config = getPluginConfig(api);
                    const result = await runPythonAction({
                        action: "odoo_write",
                        model: params.model,
                        payload: { ids: params.ids, values: params.values, confirmed: params.confirmed },
                        config,
                    });
                    return { content: [{ type: "text", text: toToolText(result) }] };
                },
            },
            { optional: true },
        );

        // ----------------------------------------------------------------
        // DELETE — policy + snapshot before delete
        // ----------------------------------------------------------------

        api.registerTool(
            {
                name: "odoo_delete",
                description:
                    "Delete records in an Odoo model. Requires explicit policy allowance. " +
                    "Pre-delete state is snapshotted. This operation is NOT reversible.",
                parameters: Type.Object({
                    model: Type.String({ description: "Odoo model name" }),
                    ids: Type.Array(Type.Number(), { description: "Record ids to delete" }),
                    confirmed: Type.Optional(Type.Boolean()),
                }),
                async execute(
                    _id: string,
                    params: { model: string; ids: number[]; confirmed?: boolean }
                ) {
                    const config = getPluginConfig(api);
                    const result = await runPythonAction({
                        action: "odoo_delete",
                        model: params.model,
                        payload: { ids: params.ids, confirmed: params.confirmed },
                        config,
                    });
                    return { content: [{ type: "text", text: toToolText(result) }] };
                },
            },
            { optional: true },
        );

        // ----------------------------------------------------------------
        // ROLLBACK — best-effort using snapshot
        // ----------------------------------------------------------------

        api.registerTool(
            {
                name: "odoo_rollback",
                description:
                    "Attempt to roll back a previous action using its snapshot. " +
                    "Only create and write operations are reversible. Delete is NOT reversible. " +
                    "Provide either snapshot_id or action_log_id.",
                parameters: Type.Object({
                    snapshot_id: Type.Optional(Type.String()),
                    action_log_id: Type.Optional(Type.String()),
                }),
                async execute(_id: string, params: { snapshot_id?: string; action_log_id?: string }) {
                    const config = getPluginConfig(api);
                    const result = await runPythonAction({
                        action: "odoo_rollback",
                        payload: { snapshot_id: params.snapshot_id, action_log_id: params.action_log_id },
                        config,
                    });
                    return { content: [{ type: "text", text: toToolText(result) }] };
                },
            },
            { optional: true },
        );
    },
});
