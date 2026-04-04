# Guide — Créer des Skills Odoo pour OpenClaw

Ce guide explique comment étendre le plugin Odoo d'OpenClaw avec des **skills** : des fichiers Markdown qui apprennent à l'IA comment interagir avec des modèles Odoo spécifiques, dans quel contexte, avec quelles précautions.

---

## Sommaire

1. [Concepts clés](#1-concepts-clés)
2. [Architecture des skills](#2-architecture-des-skills)
3. [Anatomie d'un fichier skill](#3-anatomie-dun-fichier-skill)
4. [Créer un skill pas à pas](#4-créer-un-skill-pas-à-pas)
5. [Lier un skill à des règles de permission](#5-lier-un-skill-à-des-règles-de-permission)
6. [Lier un skill à des templates](#6-lier-un-skill-à-des-templates)
7. [Catalogue de skills fournis](#7-catalogue-de-skills-fournis)
8. [Exemples complets](#8-exemples-complets)
9. [Checklist avant activation](#9-checklist-avant-activation)
10. [Erreurs fréquentes](#10-erreurs-fréquentes)

---

## 1. Concepts clés

### Pourquoi des skills ?

Le connecteur Odoo expose des outils génériques (`odoo_read`, `odoo_create`, etc.) qui fonctionnent sur **n'importe quel modèle**. Mais l'IA ne sait pas *comment* bien utiliser `crm.lead` ou `account.move` sans contexte métier.

Un **skill** est un fichier `.md` qui donne à l'IA :
- le contexte métier du modèle (à quoi ça sert, quand l'utiliser)
- les champs importants et leur signification
- les précautions à respecter (ne pas clôturer une facture sans vérification, etc.)
- les enchaînements d'actions recommandés
- les cas d'erreur courants

### Séparation des responsabilités

```
Permission rules (config OpenClaw)
    └── CE QUE l'IA peut faire (droits techniques)

Skills (fichiers .md)
    └── COMMENT l'IA doit le faire (connaissance métier)
```

Les skills ne remplacent pas les règles de permission — ils les complètent.

---

## 2. Architecture des skills

```
skills/
└── odoo/
    ├── SKILL.md                    ← Skill racine (toujours chargé)
    │
    ├── crm/
    │   ├── SKILL.md                ← Skill CRM général
    │   └── crm_lead.md             ← Skill spécifique aux opportunités
    │
    ├── accounting/
    │   ├── SKILL.md                ← Skill comptabilité général
    │   ├── account_invoice.md      ← Skill factures
    │   └── account_move.md         ← Skill écritures comptables
    │
    ├── hr/
    │   ├── SKILL.md                ← Skill RH général
    │   └── hr_employee.md          ← Skill employés
    │
    ├── inventory/
    │   └── SKILL.md                ← Skill stock/inventaire
    │
    ├── sales/
    │   └── SKILL.md                ← Skill ventes
    │
    └── templates/
        ├── crm_lead.md
        ├── account_invoice.md
        └── ...
```

### Chargement des skills

OpenClaw charge automatiquement tous les fichiers `.md` du dossier `skills/` déclaré dans `openclaw.plugin.json`. Les skills sont injectés dans le contexte système de l'IA.

Pour activer un nouveau dossier de skills, ajouter son chemin dans `openclaw.plugin.json` :

```json
{
  "skills": [
    "./skills"
  ]
}
```

Tous les sous-dossiers sont parcourus récursivement.

---

## 3. Anatomie d'un fichier skill

Un skill bien construit contient les sections suivantes :

```markdown
---
name: nom-du-skill
description: Description courte (utilisée pour la sélection automatique du skill)
models:
  - nom.modele.odoo
operations:
  - read
  - create
  - write
  - delete
---

# Titre du skill

## Contexte métier
Explication de ce que représente ce modèle dans Odoo, à quoi il sert
dans le processus métier, quand l'utiliser.

## Champs importants
Description des champs clés, leur signification métier, leurs valeurs possibles.

## Règles métier
Les règles à respecter impérativement (ex : ne jamais supprimer une facture validée).

## Enchaînement recommandé
Les étapes dans l'ordre pour accomplir une tâche correctement.

## Précautions
Les erreurs courantes à éviter.

## Exemples d'utilisation
Des scénarios concrets avec les outils à appeler.
```

### Le frontmatter YAML

| Clé | Obligatoire | Description |
|-----|-------------|-------------|
| `name` | ✅ | Identifiant unique du skill |
| `description` | ✅ | Résumé court (aide OpenClaw à sélectionner le bon skill) |
| `models` | ✅ | Liste des modèles Odoo concernés |
| `operations` | ✅ | Opérations autorisées dans ce skill |

---

## 4. Créer un skill pas à pas

### Étape 1 — Identifier le besoin

Répondre à ces questions avant d'écrire :
- Quel modèle Odoo est concerné ? (`crm.lead`, `account.move`…)
- Quelles opérations l'IA doit-elle effectuer ? (lecture seule ? création ? modification ?)
- Quelles erreurs métier veut-on éviter ?
- Y a-t-il des dépendances entre champs ? (ex : un devis doit être confirmé avant facturation)

### Étape 2 — Découvrir le modèle avec l'IA

Utiliser l'outil `odoo_list_fields` pour explorer le modèle :

```
odoo_list_fields(model: "crm.lead")
```

Cela retourne tous les champs avec leur type, label, et si ils sont obligatoires.

### Étape 3 — Écrire le fichier skill

Créer `skills/odoo/<domaine>/SKILL.md` en suivant l'anatomie ci-dessus.

**Exemple minimal :**

```markdown
---
name: crm-leads
description: Gestion des leads et opportunités CRM dans Odoo
models:
  - crm.lead
operations:
  - read
  - create
  - write
---

# CRM — Leads & Opportunités

## Contexte métier
`crm.lead` représente à la fois les leads (contacts non qualifiés)
et les opportunités (prospects qualifiés avec un pipeline commercial).
Un lead peut être converti en opportunité via le champ `type`.

## Champs importants

| Champ | Type | Description |
|-------|------|-------------|
| `name` | char | Titre de l'opportunité — obligatoire |
| `partner_id` | many2one | Client lié |
| `stage_id` | many2one | Étape dans le pipeline |
| `probability` | float | Probabilité de succès (0-100) |
| `expected_revenue` | monetary | Revenu estimé |
| `user_id` | many2one | Vendeur assigné |
| `type` | selection | `lead` ou `opportunity` |

## Règles métier

- Ne pas modifier `probability` manuellement si elle est gérée automatiquement par l'IA prédictive Odoo.
- Ne jamais supprimer un lead sans vérification — préférer `active = False` (archivage).
- Un lead ne peut être converti en opportunité qu'une fois un contact associé.

## Enchaînement recommandé — Créer une opportunité

1. `odoo_read` sur `crm.team` pour récupérer l'id de l'équipe
2. `odoo_read` sur `res.partner` pour récupérer l'id du client
3. `odoo_read` sur `crm.stage` pour récupérer l'id de l'étape cible
4. `odoo_create` sur `crm.lead` avec les valeurs validées

## Précautions

- Toujours vérifier qu'un contact `partner_id` existe avant de créer une opportunité.
- Ne pas créer deux opportunités identiques pour le même client — faire un `odoo_read` avec domain `[['partner_id','=',id],['active','=',True]]` d'abord.
```

### Étape 4 — Enregistrer le skill

Placer le fichier dans `skills/odoo/<domaine>/SKILL.md`.
Si le dossier est nouveau, vérifier qu'il est couvert par la déclaration `skills` dans `openclaw.plugin.json`.

### Étape 5 — Tester

Demander à l'IA de lire le skill et d'effectuer une opération test en lecture seule pour valider la compréhension.

---

## 5. Lier un skill à des règles de permission

Un skill décrit **comment** l'IA doit agir. Les règles de permission dans la config OpenClaw définissent **ce qu'elle peut** faire. Les deux doivent être cohérents.

**Exemple — skill CRM en lecture + création d'opportunités :**

Config `openclaw.plugin.json` :

```json
{
  "permission_rules": [
    {
      "id": "crm_read_all",
      "access_profile_id": "commercial",
      "model": "crm.lead",
      "field": "*",
      "operation": "read",
      "allowed": true,
      "require_confirmation": false
    },
    {
      "id": "crm_create_name",
      "access_profile_id": "commercial",
      "model": "crm.lead",
      "field": "name",
      "operation": "create",
      "allowed": true,
      "require_confirmation": true
    },
    {
      "id": "crm_create_partner",
      "access_profile_id": "commercial",
      "model": "crm.lead",
      "field": "partner_id",
      "operation": "create",
      "allowed": true,
      "require_confirmation": true
    },
    {
      "id": "crm_create_stage",
      "access_profile_id": "commercial",
      "model": "crm.lead",
      "field": "stage_id",
      "operation": "create",
      "allowed": true,
      "require_confirmation": true
    },
    {
      "id": "crm_create_revenue",
      "access_profile_id": "commercial",
      "model": "crm.lead",
      "field": "expected_revenue",
      "operation": "create",
      "allowed": true,
      "require_confirmation": true
    }
  ]
}
```

> **Règle d'or** : chaque champ mentionné dans un skill comme "créable" ou "modifiable" doit avoir une règle de permission correspondante. Si la règle n'existe pas, l'IA recevra `AUTHORIZATION_DENIED`.

### Astuce — wildcard sur la lecture

Pour les lectures, utiliser `"field": "*"` plutôt que de lister tous les champs :

```json
{
  "id": "crm_read_all",
  "model": "crm.lead",
  "field": "*",
  "operation": "read",
  "allowed": true
}
```

Pour les écritures, **ne jamais utiliser le wildcard** — toujours lister explicitement les champs autorisés.

---

## 6. Lier un skill à des templates

Les templates Markdown (dans `skills/odoo/templates/`) peuvent être référencés dans les skills pour guider la création de contenu structuré.

**Dans le skill :**

```markdown
## Templates disponibles

Pour créer une opportunité complète, utiliser le template `crm_lead` :

- Template : `crm_lead.md`
- Action Odoo : `odoo_create` sur `crm.lead`
- Variables requises : `name`, `partner_id`, `stage_id`, `expected_revenue`
```

**Dans la config (template JSON lié à l'action) :**

```json
{
  "templates": [
    {
      "id": "crm_lead_standard",
      "label": "Opportunité standard",
      "action": "create",
      "required_variables": ["name", "partner_id", "stage_id"],
      "payload_template": {
        "name": "{name}",
        "partner_id": "{partner_id}",
        "stage_id": "{stage_id}",
        "type": "opportunity",
        "priority": "1"
      },
      "enabled": true
    }
  ]
}
```

L'IA peut alors appeler :

```
odoo_create(
  model: "crm.lead",
  template_id: "crm_lead_standard",
  variables: { name: "Projet X", partner_id: 42, stage_id: 3 }
)
```

---

## 7. Catalogue de skills fournis

| Skill | Modèle(s) Odoo | Opérations | Fichier |
|-------|---------------|------------|---------|
| CRM — Leads & Opportunités | `crm.lead` | read, create, write | `crm/SKILL.md` |
| Comptabilité — Factures | `account.move` | read, create | `accounting/SKILL.md` |
| RH — Employés | `hr.employee` | read, create, write | `hr/SKILL.md` |
| Achats — BdC | `purchase.order` | read, create | `purchases/SKILL.md` |
| Ventes — Commandes | `sale.order` | read, create | `sales/SKILL.md` |
| Produits | `product.template`, `product.product` | read, create, write | `inventory/SKILL.md` |
| Helpdesk — Tickets | `helpdesk.ticket` | read, create, write | `helpdesk/SKILL.md` |
| Projets — Tâches | `project.task`, `project.project` | read, create, write | (existant) |
| Contacts | `res.partner` | read, create, write | (existant) |

---

## 8. Exemples complets

### Skill — Comptabilité (lecture seule)

```markdown
---
name: accounting-invoices
description: Consultation des factures clients et fournisseurs dans Odoo
models:
  - account.move
  - account.move.line
operations:
  - read
---

# Comptabilité — Factures

## Contexte métier
`account.move` est le modèle central de la comptabilité Odoo.
Il couvre les factures clients (out_invoice), avoirs clients (out_refund),
factures fournisseurs (in_invoice) et avoirs fournisseurs (in_refund).

## ⚠️ Précautions critiques

- **Ne jamais modifier une écriture en état `posted`** — cela invaliderait la comptabilité.
- **Ne jamais supprimer une facture** — utiliser l'annulation (`button_cancel`) uniquement si votre instance le permet.
- Ce skill est configuré en **lecture seule** intentionnellement.

## Champs importants

| Champ | Type | Description |
|-------|------|-------------|
| `name` | char | Référence (ex : INV/2024/00001) |
| `move_type` | selection | Type : out_invoice, in_invoice, out_refund, in_refund |
| `partner_id` | many2one | Client ou fournisseur |
| `invoice_date` | date | Date de facturation |
| `invoice_date_due` | date | Date d'échéance |
| `amount_total` | monetary | Montant TTC |
| `amount_residual` | monetary | Montant restant à payer |
| `state` | selection | draft, posted, cancel |
| `payment_state` | selection | not_paid, in_payment, paid, partial, reversed |

## Enchaînements recommandés

### Consulter les factures impayées d'un client
1. `odoo_read` sur `res.partner` avec domain `[['name','ilike','Nom client']]` → récupérer `partner_id`
2. `odoo_read` sur `account.move` avec domain :
   ```
   [
     ['partner_id','=',<id>],
     ['move_type','=','out_invoice'],
     ['payment_state','in',['not_paid','partial']],
     ['state','=','posted']
   ]
   ```
   Champs : `name`, `invoice_date_due`, `amount_residual`, `currency_id`

### Vérifier le solde d'un fournisseur
1. `odoo_read` sur `account.move` avec domain :
   ```
   [['partner_id','=',<id>],['move_type','=','in_invoice'],['state','=','posted']]
   ```
```

### Skill — Helpdesk (création + modification)

```markdown
---
name: helpdesk-tickets
description: Gestion des tickets de support client dans Odoo Helpdesk
models:
  - helpdesk.ticket
operations:
  - read
  - create
  - write
---

# Helpdesk — Tickets Support

## Contexte métier
`helpdesk.ticket` représente une demande de support client.
Les tickets passent par des étapes (stage_id) définies par équipe.

## Règles métier

- Toujours vérifier qu'un ticket similaire n'existe pas avant d'en créer un.
- Ne jamais fermer un ticket sans résolution documentée.
- La priorité `3` (Urgent) doit déclencher une notification — à signaler explicitement.
- Ne pas réassigner un ticket sans informer l'agent précédent.

## Enchaînement — Créer un ticket

1. `odoo_read` sur `helpdesk.team` → récupérer l'id de l'équipe
2. `odoo_read` sur `res.partner` → récupérer ou créer le contact client
3. Vérifier les doublons : `odoo_read` sur `helpdesk.ticket` avec domain
   `[['partner_id','=',<id>],['stage_id.is_close','=',False]]`
4. Si aucun doublon → `odoo_create` sur `helpdesk.ticket`
5. Confirmer à l'utilisateur le numéro de ticket créé

## Enchaînement — Clôturer un ticket

1. `odoo_read` sur `helpdesk.ticket` → vérifier l'état actuel
2. Demander confirmation à l'utilisateur avec la résolution
3. `odoo_write` avec `{ "stage_id": <id_etape_close>, "kanban_state": "done" }`
```

---

## 9. Checklist avant activation d'un skill

Avant de déployer un nouveau skill en production :

**Côté skill (fichier .md)**
- [ ] Le frontmatter est complet (`name`, `description`, `models`, `operations`)
- [ ] Les modèles listés correspondent aux vrais noms techniques Odoo
- [ ] Les champs importants sont documentés avec leur type
- [ ] Les règles métier critiques sont clairement identifiées (⚠️)
- [ ] Les enchaînements recommandés sont testés manuellement
- [ ] Les cas d'erreur fréquents sont documentés

**Côté config OpenClaw (règles de permission)**
- [ ] Chaque opération décrite dans le skill a une règle de permission correspondante
- [ ] Les champs de création/modification sont listés un par un (pas de wildcard en écriture)
- [ ] `require_confirmation: true` sur toutes les opérations d'écriture
- [ ] Un profil d'accès dédié est créé pour ce domaine métier
- [ ] Le profil est lié au bon profil de connexion

**Côté test**
- [ ] Tester `odoo_read` en premier pour vérifier les droits
- [ ] Tester `odoo_create` avec `confirmed: false` d'abord pour vérifier la demande de confirmation
- [ ] Vérifier que `AUTHORIZATION_DENIED` est bien retourné pour les champs hors règles

---

## 10. Erreurs fréquentes

| Erreur | Cause probable | Solution |
|--------|---------------|----------|
| `AUTHORIZATION_DENIED` sur un champ | Règle de permission manquante pour ce champ | Ajouter la règle dans `permission_rules` |
| `AUTHORIZATION_DENIED` sur tous les champs | Profil d'accès mal configuré ou mauvais `active_access_profile_id` | Vérifier la liaison profil → connexion |
| `NOT_FOUND` sur le modèle | Nom technique incorrect | Utiliser `odoo_list_models` pour trouver le bon nom |
| Champs manquants dans la réponse | Le wildcard `*` sur read ne retourne pas tous les champs | Lister explicitement les champs dans `fields` |
| Création réussie mais données manquantes | Des champs obligatoires côté Odoo ne sont pas dans les règles | Vérifier avec `odoo_list_fields` les champs `required: true` |
| `CONFIRMATION_REQUIRED` en boucle | L'IA ne transmet pas `confirmed: true` | Le skill doit explicitement demander confirmation à l'utilisateur avant de relancer |

---

## Ressources complémentaires

- **Documentation Odoo** : [https://www.odoo.com/documentation/](https://www.odoo.com/documentation/)
- **Explorer les modèles** : utiliser `odoo_list_models` puis `odoo_list_fields` depuis l'IA
- **Fichiers de référence** : `skills/odoo/SKILL.md` — skill racine toujours actif
- **Templates disponibles** : `skills/odoo/templates/`
