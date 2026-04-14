# JMeter Scenarios

Ces plans rapprochent le projet de l'image de référence en utilisant **Apache JMeter** pour :

- `load testing` : [load-test-plan.jmx](/Users/stefen/api-testing/jmeter/load-test-plan.jmx)
- `stress testing` : [stress-test-plan.jmx](/Users/stefen/api-testing/jmeter/stress-test-plan.jmx)

## Variables principales

- `host=127.0.0.1`
- `port=8000`
- `protocol=http`
- `api_key=demo-secret-key`
- `threads`, `ramp_up`, `loops`

## Exécution GUI

```bash
jmeter
```

Puis ouvrir le plan voulu.

## Exécution CLI

Charge attendue :

```bash
jmeter -n -t jmeter/load-test-plan.jmx -l jmeter/load-results.jtl
```

Stress :

```bash
jmeter -n -t jmeter/stress-test-plan.jmx -l jmeter/stress-results.jtl
```

## Pré-requis

Lancer d'abord l'API :

```bash
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
