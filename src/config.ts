export type ConnectionProfileConfig = {
    id: string;
    label: string;
    base_url: string;
    database: string;
    login: string;
    auth_type: "password" | "api_key";
    secret_ref: string;
    api_mode: "jsonrpc";
    enabled: boolean;
    port?: number;
};

export type AccessProfileConfig = {
    id: string;
    label: string;
    connection_profile_id: string;
    enabled: boolean;
    default_read_confirmation: boolean;
    default_create_confirmation: boolean;
    default_write_confirmation: boolean;
    default_delete_confirmation: boolean;
};

export type PermissionRuleConfig = {
    id: string;
    access_profile_id: string;
    model: string;
    field: string;
    operation: "read" | "create" | "write" | "delete";
    allowed: boolean;
    require_confirmation?: boolean;
    template_ids?: string[];
};

export type TemplateConfig = {
    id: string;
    label: string;
    action: "create_task";
    required_variables: string[];
    payload_template: Record<string, unknown>;
    enabled: boolean;
};

export type OdooPluginConfig = {
    active_connection_profile_id: string;
    active_access_profile_id: string;
    default_limit: number;
    read_only: boolean;
    connection_profiles: ConnectionProfileConfig[];
    access_profiles: AccessProfileConfig[];
    permission_rules: PermissionRuleConfig[];
    templates: TemplateConfig[];
};

const defaultConnectionProfile: ConnectionProfileConfig = {
    id: "default",
    label: "Default connection",
    base_url: "",
    database: "",
    login: "",
    auth_type: "password",
    secret_ref: "default",
    api_mode: "jsonrpc",
    enabled: true,
    port: 443,
};

const defaultAccessProfile: AccessProfileConfig = {
    id: "readonly",
    label: "Readonly",
    connection_profile_id: "default",
    enabled: true,
    default_read_confirmation: false,
    default_create_confirmation: true,
    default_write_confirmation: true,
    default_delete_confirmation: true,
};

const defaultPermissionRules: PermissionRuleConfig[] = [
    {
        id: "readonly_project_task_read",
        access_profile_id: "readonly",
        model: "project.task",
        field: "*",
        operation: "read",
        allowed: true,
        require_confirmation: false,
    },
    {
        id: "project_ops_project_task_create",
        access_profile_id: "project_ops",
        model: "project.task",
        field: "name",
        operation: "create",
        allowed: true,
        require_confirmation: true,
    },
    {
        id: "project_ops_project_task_create_project_id",
        access_profile_id: "project_ops",
        model: "project.task",
        field: "project_id",
        operation: "create",
        allowed: true,
        require_confirmation: true,
    },
    {
        id: "project_ops_project_task_create_description",
        access_profile_id: "project_ops",
        model: "project.task",
        field: "description",
        operation: "create",
        allowed: true,
        require_confirmation: true,
    },
];

const defaultAccessProfiles: AccessProfileConfig[] = [
    defaultAccessProfile,
    {
        id: "project_ops",
        label: "Project Ops",
        connection_profile_id: "default",
        enabled: true,
        default_read_confirmation: false,
        default_create_confirmation: true,
        default_write_confirmation: true,
        default_delete_confirmation: true,
    },
];

function asArray<T>(value: unknown): T[] {
    return Array.isArray(value) ? (value as T[]) : [];
}

export function getPluginConfig(api: any): OdooPluginConfig {
    const entry = api?.pluginConfig ?? {};

    const baseUrl = entry.base_url ?? entry.baseUrl ?? "";
    const database = entry.database ?? "";
    const defaultLimit = entry.default_limit ?? entry.defaultLimit ?? 25;
    const readOnly = entry.read_only ?? entry.readOnly ?? true;

    const connectionProfiles = asArray<ConnectionProfileConfig>(entry.connection_profiles);
    const accessProfiles = asArray<AccessProfileConfig>(entry.access_profiles);
    const permissionRules = asArray<PermissionRuleConfig>(entry.permission_rules);
    const templates = asArray<TemplateConfig>(entry.templates);

    const normalizedConnectionProfiles = connectionProfiles.length
        ? connectionProfiles
        : [{ ...defaultConnectionProfile, base_url: baseUrl, database }];

    const normalizedAccessProfiles = accessProfiles.length ? accessProfiles : defaultAccessProfiles;

    return {
        active_connection_profile_id:
            entry.active_connection_profile_id ?? normalizedConnectionProfiles[0]?.id ?? "default",
        active_access_profile_id:
            entry.active_access_profile_id ?? (readOnly ? "readonly" : "project_ops"),
        default_limit: defaultLimit,
        read_only: readOnly,
        connection_profiles: normalizedConnectionProfiles,
        access_profiles: normalizedAccessProfiles,
        permission_rules: permissionRules.length ? permissionRules : defaultPermissionRules,
        templates,
    };
}
