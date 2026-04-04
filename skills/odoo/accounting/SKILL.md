---
name: accounting-invoices
description: Consultation des factures et écritures comptables Odoo — lecture seule
models:
  - account.move
  - account.move.line
  - account.payment
operations:
  - read
---

# Comptabilité — Factures & Paiements

## Contexte métier

`account.move` est le modèle central de toute la comptabilité Odoo.
Il couvre : factures clients, avoirs clients, factures fournisseurs, avoirs fournisseurs, et écritures manuelles.

> Ce skill est intentionnellement **lecture seule**. La comptabilité est un domaine réglementé — toute modification doit passer par un comptable qualifié.

## Champs importants

| Champ | Description |
|-------|-------------|
| `name` | Référence (INV/2024/00001) |
| `move_type` | `out_invoice` / `out_refund` / `in_invoice` / `in_refund` / `entry` |
| `partner_id` | Client ou fournisseur |
| `invoice_date` | Date de facturation |
| `invoice_date_due` | Date d'échéance |
| `amount_untaxed` | Montant HT |
| `amount_total` | Montant TTC |
| `amount_residual` | Reste à payer |
| `state` | `draft` / `posted` / `cancel` |
| `payment_state` | `not_paid` / `in_payment` / `paid` / `partial` / `reversed` |
| `invoice_origin` | Référence de la commande source |
| `journal_id` | Journal comptable |

## ⚠️ Règles critiques

- **Ne jamais tenter de modifier un `account.move` en état `posted`**.
- **Ne jamais supprimer une facture** — même en brouillon, préférer l'annulation.
- Ne pas exposer les `account.move.line` (écritures analytiques) sans confirmation du contexte.
- Les montants sont toujours dans la devise de la société (`company_currency_id`).

## Enchaînements recommandés

### Factures impayées d'un client
```
odoo_read(account.move,
  domain=[
    ['partner_id','=',<id>],
    ['move_type','=','out_invoice'],
    ['state','=','posted'],
    ['payment_state','in',['not_paid','partial']]
  ],
  fields=['name','invoice_date_due','amount_residual','currency_id']
)
```

### Solde fournisseur
```
odoo_read(account.move,
  domain=[
    ['partner_id','=',<id>],
    ['move_type','=','in_invoice'],
    ['state','=','posted'],
    ['payment_state','!=','paid']
  ],
  fields=['name','invoice_date_due','amount_residual']
)
```

### Paiements reçus d'un client
```
odoo_read(account.payment,
  domain=[
    ['partner_id','=',<id>],
    ['payment_type','=','inbound'],
    ['state','=','posted']
  ],
  fields=['name','date','amount','currency_id','state']
)
```

## Précautions

- Toujours préciser le `move_type` dans les domains pour éviter des résultats mixtes.
- Les factures en `draft` ne sont pas comptabilisées — le distinguer clairement.
- `amount_residual` peut être négatif pour les avoirs — interpréter avec soin.
