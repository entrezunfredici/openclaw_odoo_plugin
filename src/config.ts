export type OdooPluginConfig = {
    baseUrl: string;
    database: string;
    profile: "readonly" | "project_ops";
    readOnly: boolean;
    defaultLimit: number;
};

export function getPluginConfig(api: any): OdooPluginConfig {
    const entry = api?.pluginConfig ?? {};

    return {
        baseUrl: entry.baseUrl ?? "",
        database: entry.database ?? "",
        profile: entry.profile ?? "readonly",
        readOnly: entry.readOnly ?? true,
        defaultLimit: entry.defaultLimit ?? 25
    };
}
