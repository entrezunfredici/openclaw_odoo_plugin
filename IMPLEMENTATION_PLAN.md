## Implementation Plan

1. Align the plugin entrypoint with the requested bounded CRUD surface:
   - expose `odoo_read`, `odoo_create`, `odoo_update`, `odoo_delete`
   - accept explicit profile selection in tool parameters
   - keep authorization deny-by-default through configured rules

2. Keep configuration structured and explicit:
   - `ConnectionProfile`
   - `AccessProfile`
   - `PermissionRule`
   - `Template`

3. Tighten the Python backend flow:
   - central payload validation before execution
   - `odoo_update` support mapped to write semantics
   - `create_task` validation and template binding checks
   - snapshot creation before write execution
   - action logging and reversibility metadata on write flows

4. Keep rollback honest:
   - expose reversibility metadata
   - keep rollback execution stubbed for now

5. Update documentation and add targeted tests.
