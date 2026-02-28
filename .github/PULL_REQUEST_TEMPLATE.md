## Summary
<!-- Décris ce que fait cette PR en 2-3 phrases -->

## Issue
Closes #<!-- ISSUE_ID — cette ligne est OBLIGATOIRE. L'autoqueue en dépend pour chaîner la prochaine issue. -->

## Changes
- <!-- fichier créé/modifié -->
- <!-- fichier créé/modifié -->

## Migration
- <!-- Nom de la migration si applicable, ex: connect/migrations/0001_initial.py -->
- N/A si aucune migration

## CI Checklist
- [ ] `python -m compileall apps/backend/src -q` ✅
- [ ] `python manage.py check` ✅
- [ ] `python manage.py migrate --noinput` ✅ (si migration)
- [ ] Aucun `print()` dans le code ajouté — utiliser `logging`
- [ ] Aucune clé Stripe en dur
- [ ] Aucun `raise Exception(...)` au top-level de module
- [ ] `application_fee_percent=20` si Stripe Connect (jamais `settings.PLATFORM_FEE_PERCENT`)
