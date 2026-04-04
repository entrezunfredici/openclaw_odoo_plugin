---
name: inventory-stock
description: Consultation du stock, des mouvements et des réassorts dans Odoo Inventory
models:
  - stock.quant
  - stock.move
  - stock.picking
  - product.product
  - product.template
operations:
  - read
---

# Inventaire & Stock

## Contexte métier

Le module Inventory gère les mouvements physiques de marchandises :
- `stock.quant` → quantités réelles en stock par emplacement
- `stock.picking` → bons de livraison, réceptions, transferts internes
- `stock.move` → lignes de mouvement individuelles
- `product.product` → variante de produit (avec attributs)
- `product.template` → fiche produit générique

> Ce skill est en lecture seule. Les ajustements d'inventaire doivent être validés par le gestionnaire de stock.

## Champs importants

### stock.quant (quantités en stock)
| Champ | Description |
|-------|-------------|
| `product_id` | Produit (variante) |
| `location_id` | Emplacement physique |
| `quantity` | Quantité disponible |
| `reserved_quantity` | Quantité réservée |
| `available_quantity` | Quantité disponible nette |

### stock.picking (transferts)
| Champ | Description |
|-------|-------------|
| `name` | Référence (WH/IN/00001) |
| `picking_type_id` | Type : réception / livraison / interne |
| `partner_id` | Fournisseur ou client |
| `origin` | Commande source |
| `scheduled_date` | Date prévue |
| `state` | `draft` / `waiting` / `confirmed` / `assigned` / `done` / `cancel` |
| `move_ids` | Lignes de mouvement |

## Enchaînements recommandés

### Stock disponible d'un produit
```
1. odoo_read(product.product, [['name','ilike','Nom']])
   → récupérer product_id

2. odoo_read(stock.quant,
     [['product_id','=',<id>],['location_id.usage','=','internal']],
     fields=['location_id','quantity','reserved_quantity','available_quantity']
   )
```

### Réceptions en attente
```
odoo_read(stock.picking,
  domain=[
    ['picking_type_code','=','incoming'],
    ['state','in',['assigned','confirmed','waiting']]
  ],
  fields=['name','partner_id','scheduled_date','state','origin']
)
```

### Livraisons à préparer aujourd'hui
```
odoo_read(stock.picking,
  domain=[
    ['picking_type_code','=','outgoing'],
    ['state','in',['assigned','confirmed']],
    ['scheduled_date','<=','<date_du_jour>']
  ],
  fields=['name','partner_id','scheduled_date','state']
)
```

## Précautions

- `stock.quant` donne la quantité **par emplacement**. Additionner les lignes pour le total global.
- Ne jamais tenter de modifier directement `stock.quant` — passer par un ajustement d'inventaire officiel.
- `available_quantity` = `quantity` - `reserved_quantity`.
- Les emplacements virtuels (`location_id.usage = 'virtual'`) ne correspondent pas à du stock physique.
