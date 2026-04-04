---
name: hr-employees
description: Consultation et gestion des employés dans Odoo HR
models:
  - hr.employee
  - hr.department
  - hr.job
  - hr.leave
  - hr.leave.allocation
operations:
  - read
  - create
  - write
---

# RH — Employés & Absences

## Contexte métier

Le module RH Odoo gère les fiches employés, les contrats, les absences et les évaluations.

> ⚠️ Les données RH sont **confidentielles**. Ne jamais afficher des données personnelles (salaire, n° sécurité sociale, adresse privée) sans que l'utilisateur l'ait explicitement demandé dans un contexte RH autorisé.

## Modèles couverts

| Modèle | Description |
|--------|-------------|
| `hr.employee` | Fiche employé complète |
| `hr.department` | Département / service |
| `hr.job` | Poste de travail |
| `hr.leave` | Demande d'absence (congé, RTT…) |
| `hr.leave.allocation` | Attribution de jours de congé |

## Champs importants — hr.employee

| Champ | Sensible | Description |
|-------|----------|-------------|
| `name` | | Nom complet |
| `job_id` | | Poste |
| `department_id` | | Département |
| `parent_id` | | Responsable hiérarchique |
| `work_email` | | Email professionnel |
| `work_phone` | | Téléphone professionnel |
| `resource_calendar_id` | | Horaire de travail |
| `active` | | `False` = archivé (ex-employé) |
| `private_email` | ⚠️ | Email personnel — accès restreint |
| `ssnid` | ⚠️ | N° sécurité sociale — accès restreint |
| `address_home_id` | ⚠️ | Adresse privée — accès restreint |

## ⚠️ Règles critiques

- **Ne jamais afficher `ssnid`, `private_email`, `address_home_id`** sans demande RH explicite.
- **Ne jamais archiver un employé (`active=False`)** sans confirmation de la direction RH.
- Ne pas modifier le `parent_id` (responsable) sans validation managériale.
- Les absences validées ne doivent pas être modifiées directement — utiliser les workflows Odoo.

## Enchaînements recommandés

### Trouver un employé
```
odoo_read(hr.employee,
  domain=[['name','ilike','Nom'],['active','=',True]],
  fields=['name','job_id','department_id','work_email','parent_id']
)
```

### Lister les employés d'un département
```
1. odoo_read(hr.department, [['name','ilike','Dept']])
   → récupérer department_id

2. odoo_read(hr.employee,
     [['department_id','=',<id>],['active','=',True]],
     fields=['name','job_id','work_email','resource_calendar_id']
   )
```

### Absences en cours
```
odoo_read(hr.leave,
  domain=[
    ['employee_id','=',<id>],
    ['state','=','validate'],
    ['date_from','<=','<aujourd_hui>'],
    ['date_to','>=','<aujourd_hui>']
  ],
  fields=['holiday_status_id','date_from','date_to','number_of_days','state']
)
```

## Précautions

- `active = False` signifie l'employé est archivé (ex-employé). Toujours filtrer `['active','=',True]` par défaut.
- Les soldes de congés sont dans `hr.leave.allocation` — ce n'est pas `hr.leave`.
- Un employé peut avoir plusieurs contrats — utiliser `hr.contract` pour les détails contractuels.
