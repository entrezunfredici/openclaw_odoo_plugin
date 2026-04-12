import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { getPluginConfig } from "./config.js";
import { runPythonAction } from "./pythonBridge.js";

function toToolText(result: unknown): string {
    return JSON.stringify(result, null, 2);
}

const profileSelectionSchema = Type.Object({
    connection_profile_id: Type.String({
        description: "Configured connection profile id",
    }),
    access_profile_id: Type.Optional(
        Type.String({
            description: "Configured access profile id. Defaults to the active access profile if omitted.",
        }),
    ),
});

type ToolProfileSelection = {
    connection_profile_id: string;
    access_profile_id?: string;
};

function buildProfilePayload(profile: ToolProfileSelection): Record<string, unknown> {
    return {
        connection_profile_id: profile.connection_profile_id,
        access_profile_id: profile.access_profile_id,
    };
}

export default definePluginEntry({
    id: "odoo-plugin",
    name: "Odoo Plugin",
    description: "Policy-enforced Odoo connector with four bounded CRUD tools",

    register(api: any) {
        api.registerTool({
            name: "odoo_read",
            description:
                "Read records from an allowed Odoo model. Access is denied by default and " +
                "evaluated per (model, field, operation).",
            parameters: Type.Object({
                profile: profileSelectionSchema,
                model: Type.String({ description: "Odoo model name, e.g. 'project.task'" }),
                fields: Type.Optional(
                    Type.Array(Type.String(), { description: "Fields to read. Defaults to ['id', 'name']." }),
                ),
                filters: Type.Optional(
                    Type.Array(Type.Any(), { description: "Odoo domain filter, e.g. [['project_id', '=', 1]]" }),
                ),
                limit: Type.Optional(Type.Number({ description: "Max records to return" })),
            }),
            async execute(
                _id: string,
                params: {
                    profile: ToolProfileSelection;
                    model: string;
                    fields?: string[];
                    filters?: unknown[];
                    limit?: number;
                },
            ) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_read",
                    model: params.model,
                    payload: {
                        ...buildProfilePayload(params.profile),
                        fields: params.fields,
                        filters: params.filters,
                        limit: params.limit,
                    },
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });

        api.registerTool({
            name: "odoo_create",
            description:
                "Create a record in an allowed Odoo model. Field-level permissions, confirmation " +
                "requirements, snapshots, and action logs are enforced by the backend.",
            parameters: Type.Object({
                profile: profileSelectionSchema,
                model: Type.String({ description: "Odoo model name" }),
                data: Type.Optional(
                    Type.Record(Type.String(), Type.Any(), {
                        description: "Field values to set on the new record",
                    }),
                ),
                template_id: Type.Optional(Type.String({ description: "Template id to render before create" })),
                variables: Type.Optional(
                    Type.Record(Type.String(), Type.Any(), { description: "Variables used by the template" }),
                ),
                confirmed: Type.Optional(
                    Type.Boolean({ description: "Set true after the user explicitly confirms the write" }),
                ),
            }),
            async execute(
                _id: string,
                params: {
                    profile: ToolProfileSelection;
                    model: string;
                    data?: Record<string, unknown>;
                    template_id?: string;
                    variables?: Record<string, unknown>;
                    confirmed?: boolean;
                },
            ) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_create",
                    model: params.model,
                    payload: {
                        ...buildProfilePayload(params.profile),
                        values: params.data,
                        template_id: params.template_id,
                        variables: params.variables,
                        confirmed: params.confirmed,
                    },
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });

        api.registerTool({
            name: "odoo_update",
            description:
                "Update one record in an allowed Odoo model. Authorization is evaluated per field " +
                "and the previous state is snapshotted before execution.",
            parameters: Type.Object({
                profile: profileSelectionSchema,
                model: Type.String({ description: "Odoo model name" }),
                id: Type.Number({ description: "Record id to update" }),
                data: Type.Record(Type.String(), Type.Any(), { description: "Fields to update" }),
                confirmed: Type.Optional(
                    Type.Boolean({ description: "Set true after the user explicitly confirms the write" }),
                ),
            }),
            async execute(
                _id: string,
                params: {
                    profile: ToolProfileSelection;
                    model: string;
                    id: number;
                    data: Record<string, unknown>;
                    confirmed?: boolean;
                },
            ) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_update",
                    model: params.model,
                    payload: {
                        ...buildProfilePayload(params.profile),
                        id: params.id,
                        values: params.data,
                        confirmed: params.confirmed,
                    },
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });

        api.registerTool({
            name: "odoo_delete",
            description:
                "Delete one record in an allowed Odoo model. Delete stays deny-by-default, " +
                "confirmation-aware, and pre-delete state is snapshotted.",
            parameters: Type.Object({
                profile: profileSelectionSchema,
                model: Type.String({ description: "Odoo model name" }),
                id: Type.Number({ description: "Record id to delete" }),
                confirmed: Type.Optional(
                    Type.Boolean({ description: "Set true after the user explicitly confirms the delete" }),
                ),
            }),
            async execute(
                _id: string,
                params: {
                    profile: ToolProfileSelection;
                    model: string;
                    id: number;
                    confirmed?: boolean;
                },
            ) {
                const config = getPluginConfig(api);
                const result = await runPythonAction({
                    action: "odoo_delete",
                    model: params.model,
                    payload: {
                        ...buildProfilePayload(params.profile),
                        id: params.id,
                        confirmed: params.confirmed,
                    },
                    config,
                });
                return { content: [{ type: "text", text: toToolText(result) }] };
            },
        });
    },
});
