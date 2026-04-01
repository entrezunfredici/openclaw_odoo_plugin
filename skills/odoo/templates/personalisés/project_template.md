# {{project_name}}

## Templates
Templates de taches disponibles dans le projet:
{{templates_section}}

## Cadrage
Templates de cadrage prevus:
{{cadrage_section}}

## Etapes des taches
<!-- Format: - template.md: etape | 1.0-2.0 | deps: autre_template.md, encore_un_template.md -->
- prod_description_project_task.md: cadrage
- prod_analyse_besoin_task.md: cadrage | deps: prod_description_project_task.md
- prod_problematique_task.md: cadrage | deps: prod_analyse_besoin_task.md
- gov_parties_prenantes_task.md: cadrage | deps: prod_problematique_task.md
- prod_moscow_fonctionnalites_task.md: cadrage | deps: gov_parties_prenantes_task.md
- prod_personas_user_stories_task.md: cadrage | deps: prod_moscow_fonctionnalites_task.md
- prod_decoupage_mvp_versions_task.md: cadrage | deps: prod_personas_user_stories_task.md
- arch_benchmark_architecture_task.md: cadrage | deps: prod_decoupage_mvp_versions_task.md
- risk_faisabilite_risques_task.md: cadrage | deps: arch_benchmark_architecture_task.md
- research_veille_techno_task.md: cadrage | deps: risk_faisabilite_risques_task.md
- prod_estimation_charge_task.md.md: cadrage | deps: research_veille_techno_task.md

## Specifications
- Architecture technique
- Contraintes et hypotheses
- Criteres d'acceptation

## En cours
- Backlog de sprint
- Tickets en execution
- Suivi de progression
