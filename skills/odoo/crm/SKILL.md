---
name: crm-leads-opportunities
description: Gestion des leads et opportunités CRM Odoo — lecture, création, modification
models:
  - crm.lead
  - crm.stage
  - crm.team
operations:
  - read
  - create
  - write
---

# CRM — Leads & Opportunités

## Contexte métier

`crm.lead` est le modèle central du CRM Odoo. Il représente à la fois :
- les **leads** (`type = lead`) : contacts non qualifiés entrants
- les **opportunités** (`type = opportunity`) : prospects qualifiés dans le pipeline commercial

Toute interaction commerciale avec un prospect passe par ce modèle.

## Champs importants

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `name` | char | ✅ | Titre de l'opportunité |
| `partner_id` | many2one | | Client lié (`res.partner`) |
| `partner_name` | char | | Nom si pas encore dans les contacts |
| `email_from` | char | | Email du contact |
| `phone` | char | | Téléphone |
| `stage_id` | many2one | ✅ | Étape du pipeline |
| `user_id` | many2one | | Vendeur assigné |
| `team_id` | many2one | | Équipe commerciale |
| `type` | selection | | `lead` ou `opportunity` |
| `probability` | float | | Probabilité (0-100%) |
| `expected_revenue` | monetary | | Revenu estimé |
| `date_deadline` | date | | Date de clôture prévue |
| `priority` | selection | | `0` Normal / `1` Low / `2` High / `3` Very High |
| `tag_ids` | many2many | | Étiquettes |
| `active` | boolean | | `False` = archivé |

## Règles métier

- ⚠️ **Ne jamais supprimer un lead** — utiliser `active = False` pour archiver.
- ⚠️ **Vérifier les doublons** avant toute création (même email ou même société).
- Un lead doit avoir `partner_id` ou `partner_name` + `email_from` au minimum.
- Ne pas modifier `probability` si l'IA prédictive Odoo est activée.
- Toujours informer l'utilisateur avant de réassigner (`user_id`).

## Enchaînement recommandé — Créer une opportunité

```
1. odoo_read(crm.team)                          → récupérer team_id
2. odoo_read(res.partner, [['name','ilike',X]]) → trouver le client
3. odoo_read(crm.stage, [['team_id','=',id]])   → récupérer les étapes
4. Vérifier doublons : odoo_read(crm.lead,
     [['partner_id','=',id],['active','=',True]])
5. odoo_create(crm.lead, values, confirmed=True)
```

## Enchaînement recommandé — Passer une opportunité à l'étape suivante

```
1. odoo_read(crm.lead, [['id','=',id]], ['stage_id','name'])
2. odoo_read(crm.stage, [['sequence','>',current_sequence]])
3. Confirmer avec l'utilisateur
4. odoo_write(crm.lead, ids=[id], values={stage_id: next_id})
```

## Précautions

- Toujours faire un `odoo_read` avant un `odoo_write` pour afficher l'état actuel.
- Si `CONFIRMATION_REQUIRED` : présenter les valeurs à l'utilisateur, attendre validation explicite, puis relancer avec `confirmed: true`.
- Ne jamais présumer de l'`expected_revenue` — toujours demander à l'utilisateur.
