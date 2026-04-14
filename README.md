# API Testing Demo V2

Projet de démonstration qui couvre les **11 catégories** de tests API sur une stack plus réaliste :

- **API métier** FastAPI
- **auth service** séparé qui émet de vrais **JWT Bearer**
- **notification service** séparé appelé par l'API
- **base SQL** locale en SQLite pour le dev/tests
- **Postgres** en environnement Docker Compose
- **Playwright** pour le vrai navigateur
- **JMeter** pour charge et stress
- **profil ZAP** pour un scan sécurité offensif de base

## Les 11 tests couverts

| # | Type | Objectif | Implémentation principale |
| --- | --- | --- | --- |
| 1 | `Smoke Testing` | Vérifier rapidement que l'API répond et que les endpoints de base sont vivants. | `tests/test_smoke.py` |
| 2 | `Functional Testing` | Valider les comportements métier attendus de création et lecture de commandes. | `tests/test_functional.py` |
| 3 | `Integration Testing` | Vérifier l'interaction entre API, base SQL et service de notification. | `tests/test_integration.py` |
| 4 | `Regression Testing` | S'assurer que les changements ne cassent pas des comportements déjà validés. | `tests/test_regression.py` |
| 5 | `Load Testing` | Mesurer le comportement de l'API sous charge attendue. | `jmeter/load-test-plan.jmx` |
| 6 | `Stress Testing` | Pousser l'API sous forte charge pour observer sa tenue en limite. | `jmeter/stress-test-plan.jmx` |
| 7 | `Security Testing` | Vérifier l'authentification, les rejets de payloads dangereux et l'exposition des données. | `tests/test_security.py` |
| 8 | `UI Testing` | Valider le lien entre l'interface `/dashboard` et les endpoints API. | `tests/test_ui.py` et `playwright/tests/dashboard.spec.js` |
| 9 | `Fuzz Testing` | Envoyer des données invalides ou aléatoires pour vérifier la robustesse de l'API. | `tests/test_fuzz.py` |
| 10 | `Reliability Testing` | Contrôler la stabilité et la cohérence de l'API sur des appels répétés. | `tests/test_reliability.py` |
| 11 | `Contract Testing` | Vérifier que les réponses JSON respectent les schémas attendus. | `tests/test_contract.py` |

## Architecture

| Composant | Rôle |
| --- | --- |
| `app.main` | API métier exposant `/api/items`, `/api/orders`, `/api/dashboard-data`, `/dashboard` |
| `services/auth_service` | Service d'auth qui émet des JWT via `/oauth/token` |
| `services/notification_service` | Microservice appelé à chaque création de commande |
| `Postgres` | Base externe dans Docker Compose |
| `SQLite` | Fallback local pour exécuter vite les tests hors Docker |
| `JMeter` | Tests `load` et `stress` |
| `Playwright` | Tests UI navigateur |
| `ZAP` | Scan sécurité via profil Docker Compose |

## Structure

```text
Makefile
app/
services/
shared/
contracts/
jmeter/
playwright/
tests/
docker/
docker-compose.yml
requirements-docker.txt
```

## Auth

Le projet utilise un **Bearer JWT** signé en `HS256`.

Utilisateurs de démonstration :

| Utilisateur | Mot de passe | Usage |
| --- | --- | --- |
| `tester` | `tester-password` | création de commandes |
| `admin` | `admin-password` | opérations d'administration si besoin |

Clé de reset pour les endpoints de test :

```text
demo-reset-key
```

## Démarrage local simple

API seule :

```bash
make run
```

Générer un token local :

```bash
make token
```

Exemple d'obtention d'un token depuis le service d'auth :

```bash
curl -X POST http://127.0.0.1:8001/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"tester","password":"tester-password"}'
```

Exemple de création de commande avec JWT :

```bash
curl -X POST http://127.0.0.1:8000/api/orders \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"item_id":"coffee","quantity":1,"customer_email":"demo@example.com"}'
```

Reset d'état pour les scénarios de test :

```bash
curl -X POST 'http://127.0.0.1:8000/api/test/reset?stock_multiplier=1' \
  -H 'X-Test-Reset-Key: demo-reset-key'
```

## Docker Compose

Démarrer la stack réaliste :

```bash
make docker-up
```

Arrêter la stack :

```bash
make docker-down
```

Afficher les logs :

```bash
make docker-logs
```

Lancer le scan ZAP :

```bash
make docker-zap
```

Services exposés :

| Service | URL |
| --- | --- |
| API | `http://127.0.0.1:8000` |
| Auth | `http://127.0.0.1:8001` |
| Notification | `http://127.0.0.1:8002` |
| Postgres | `127.0.0.1:5432` |

## Commandes de test

Suite `pytest` complète :

```bash
make test
```

Sans la suite `reliability` :

```bash
make test-fast
```

Tests UI navigateur :

```bash
make ui-install
make test-ui
```

Charge :

```bash
curl -X POST 'http://127.0.0.1:8000/api/test/reset?stock_multiplier=25' \
  -H 'X-Test-Reset-Key: demo-reset-key'
make load
```

Stress :

```bash
curl -X POST 'http://127.0.0.1:8000/api/test/reset?stock_multiplier=100' \
  -H 'X-Test-Reset-Key: demo-reset-key'
make stress
```

## Mapping des 11 types

| Type | Implémentation |
| --- | --- |
| Smoke | [tests/test_smoke.py](/Users/stefen/api-testing/tests/test_smoke.py) |
| Functional | [tests/test_functional.py](/Users/stefen/api-testing/tests/test_functional.py) |
| Integration | [tests/test_integration.py](/Users/stefen/api-testing/tests/test_integration.py) |
| Regression | [tests/test_regression.py](/Users/stefen/api-testing/tests/test_regression.py) |
| Load | [jmeter/load-test-plan.jmx](/Users/stefen/api-testing/jmeter/load-test-plan.jmx) |
| Stress | [jmeter/stress-test-plan.jmx](/Users/stefen/api-testing/jmeter/stress-test-plan.jmx) |
| Security | [tests/test_security.py](/Users/stefen/api-testing/tests/test_security.py) |
| UI | [playwright/tests/dashboard.spec.js](/Users/stefen/api-testing/playwright/tests/dashboard.spec.js) |
| Fuzz | [tests/test_fuzz.py](/Users/stefen/api-testing/tests/test_fuzz.py) |
| Reliability | [tests/test_reliability.py](/Users/stefen/api-testing/tests/test_reliability.py) |
| Contract | [tests/test_contract.py](/Users/stefen/api-testing/tests/test_contract.py) |

## Rapport de validation

Campagne exécutée localement le **14 avril 2026** après passage à la V2.

### Périmètre validé

| Élément | Statut |
| --- | --- |
| API HTTP réelle | `OK` |
| Auth JWT réelle | `OK` |
| Notification microservice | `OK` |
| Persistance SQL | `OK` |
| Docker Compose | `config validée` |
| Playwright | `OK` |
| JMeter load | `OK` |
| JMeter stress | `OK` |

### Résultats observés

| Vérification | Commande | Résultat |
| --- | --- | --- |
| Suite API | `make test` | `19 passed in 10.86s` |
| Suite UI navigateur | `npm run ui:test -- --reporter=line` | `2 passed (8.3s)` |
| Load | `make load` | `900 samples`, `92.7/s`, `0.00% error` |
| Stress | `make stress` | `4800 samples`, `258.5/s`, `0.00% error` |
| Compose | `docker compose config` | `OK` |

### Lecture

| Axe | Conclusion |
| --- | --- |
| Métier | Les flux de commande, lecture et validation passent. |
| Sécurité | Les écritures exigent un JWT Bearer valide ; les tests défensifs passent. |
| Intégration | L'API dialogue bien avec le service de notification et la persistance SQL. |
| UI | Le dashboard est validé dans un vrai navigateur Chromium. |
| Performance | Les plans JMeter passent en local sans erreur sur la campagne finale. |
| Orchestration | La stack Docker Compose est définie et valide syntaxiquement. |

### Risques résiduels

| Risque | Impact | Commentaire |
| --- | --- | --- |
| Local perf sur SQLite | Moyen | Les runs locaux hors Docker utilisent SQLite ; la cible réaliste de perf reste Postgres via Compose. |
| Auth de démo | Moyen | JWT réel, mais sans provider OIDC complet type Keycloak. |
| Notification service simple | Faible | Le service distribué est réel mais minimaliste. |
| Scan sécurité de base | Moyen | Le profil ZAP fournit un premier niveau, pas un audit offensif complet. |

### Go / No-Go

| Décision | Portée |
| --- | --- |
| `GO` | Démonstration avancée, atelier, base de projet de test réaliste |
| `NO-GO` | Production directe sans observabilité, secrets gérés, CI/CD, OIDC complet, durcissement sécurité |

### Captures par suite

Le dépôt contient maintenant une **capture PNG par suite exécutée**. Il y a **12 captures** pour **11 types** car l'axe `UI` est couvert à deux niveaux :

- `UI HTTP Wiring` via `pytest`
- `UI Browser Playwright` via un vrai navigateur

Vue globale :

- [validation-report.png](./docs/screenshots/validation-report.png)
- [report.html](./docs/validation/report.html)

| Suite | Résultat observé | Capture | Sortie brute |
| --- | --- | --- | --- |
| Smoke | `2 passed in 3.41s` | [smoke-output.png](./docs/screenshots/smoke-output.png) | [smoke.txt](./docs/validation/raw/smoke.txt) |
| Functional | `3 passed in 4.93s` | [functional-output.png](./docs/screenshots/functional-output.png) | [functional.txt](./docs/validation/raw/functional.txt) |
| Integration | `2 passed in 4.75s` | [integration-output.png](./docs/screenshots/integration-output.png) | [integration.txt](./docs/validation/raw/integration.txt) |
| Regression | `2 passed in 4.83s` | [regression-output.png](./docs/screenshots/regression-output.png) | [regression.txt](./docs/validation/raw/regression.txt) |
| Security | `4 passed in 4.78s` | [security-output.png](./docs/screenshots/security-output.png) | [security.txt](./docs/validation/raw/security.txt) |
| UI HTTP Wiring | `2 passed in 4.78s` | [ui-http-output.png](./docs/screenshots/ui-http-output.png) | [ui-http.txt](./docs/validation/raw/ui-http.txt) |
| Fuzz | `1 passed in 4.52s` | [fuzz-output.png](./docs/screenshots/fuzz-output.png) | [fuzz.txt](./docs/validation/raw/fuzz.txt) |
| Reliability | `1 passed in 6.20s` | [reliability-output.png](./docs/screenshots/reliability-output.png) | [reliability.txt](./docs/validation/raw/reliability.txt) |
| Contract | `2 passed in 4.71s` | [contract-output.png](./docs/screenshots/contract-output.png) | [contract.txt](./docs/validation/raw/contract.txt) |
| UI Browser Playwright | `2 passed (6.4s)` | [ui-browser-output.png](./docs/screenshots/ui-browser-output.png) | [ui-browser.txt](./docs/validation/raw/ui-browser.txt) |
| Load | `900 samples`, `93.2/s`, `0.00% error` | [load-output.png](./docs/screenshots/load-output.png) | [load.txt](./docs/validation/raw/load.txt) |
| Stress | `4800 samples`, `271.1/s`, `0.00% error` | [stress-output.png](./docs/screenshots/stress-output.png) | [stress.txt](./docs/validation/raw/stress.txt) |

#### Vue globale

![Validation report](./docs/screenshots/validation-report.png)

#### Smoke

![Smoke output](./docs/screenshots/smoke-output.png)

#### Functional

![Functional output](./docs/screenshots/functional-output.png)

#### Integration

![Integration output](./docs/screenshots/integration-output.png)

#### Regression

![Regression output](./docs/screenshots/regression-output.png)

#### Security

![Security output](./docs/screenshots/security-output.png)

#### UI HTTP Wiring

![UI HTTP output](./docs/screenshots/ui-http-output.png)

#### Fuzz

![Fuzz output](./docs/screenshots/fuzz-output.png)

#### Reliability

![Reliability output](./docs/screenshots/reliability-output.png)

#### Contract

![Contract output](./docs/screenshots/contract-output.png)

#### UI Browser Playwright

![UI Browser output](./docs/screenshots/ui-browser-output.png)

#### Load

![Load output](./docs/screenshots/load-output.png)

#### Stress

![Stress output](./docs/screenshots/stress-output.png)

## Fichiers clés V2

- API : [app/main.py](/Users/stefen/api-testing/app/main.py)
- Persistance : [app/store.py](/Users/stefen/api-testing/app/store.py)
- Base SQLAlchemy : [app/database.py](/Users/stefen/api-testing/app/database.py)
- Modèles SQL : [app/sql_models.py](/Users/stefen/api-testing/app/sql_models.py)
- Config : [app/settings.py](/Users/stefen/api-testing/app/settings.py)
- JWT partagé : [shared/jwt_utils.py](/Users/stefen/api-testing/shared/jwt_utils.py)
- Auth service : [services/auth_service/main.py](/Users/stefen/api-testing/services/auth_service/main.py)
- Notification service : [services/notification_service/main.py](/Users/stefen/api-testing/services/notification_service/main.py)
- Compose : [docker-compose.yml](/Users/stefen/api-testing/docker-compose.yml)
- Dockerfile services : [docker/python-service.Dockerfile](/Users/stefen/api-testing/docker/python-service.Dockerfile)
- Génération de token : [scripts/issue_demo_token.py](/Users/stefen/api-testing/scripts/issue_demo_token.py)

## Notes

- Les tests `pytest` démarrent une vraie mini-stack locale : auth, notification, API.
- `make run` lance seulement l'API ; la stack complète réaliste est `make docker-up`.
- Les plans `JMeter` embarquent un JWT de démonstration longue durée pour le mode local ; il peut être remplacé si vous changez le secret.
