# Sim Market Lab

Tracker gratuito para historial de precios de mercado de Sim Companies y detector de fases por producto.

## Qué hace la V0.1

- Consulta el `market ticker` público de Sim Companies.
- Guarda histórico de precio mínimo por producto/calidad.
- Calcula percentil histórico y fase de mercado.
- Genera CSVs que podés abrir en Excel, Google Sheets o en la app local Streamlit.
- No usa cookies, no usa login, no compra, no vende, no toca tu cuenta.

## Advertencia importante

Sim Companies permite solo llamadas GET y pide no hacer más de una petición cada 5 minutos. Esta app viene configurada cada 6 minutos, por encima del mínimo de 5 minutos. Si el endpoint cambia, editá `config/settings.json`.

## Estructura

```text
sim-market-lab/
├─ collector.py                 # recolector que corre en GitHub Actions
├─ app.py                       # dashboard local Streamlit
├─ requirements.txt
├─ config/
│  ├─ settings.json             # endpoint y configuración
│  └─ products.csv              # mapa opcional de id producto → nombre
├─ data/
│  ├─ market_ticks.csv          # historial crudo
│  └─ product_phase_latest.csv  # fase actual por producto/calidad
└─ .github/workflows/
   └─ collect.yml               # cron gratuito con GitHub Actions
```

## Cómo usarlo localmente

1. Instalá Python 3.11+.
2. Abrí una terminal en esta carpeta.
3. Ejecutá:

```bash
pip install -r requirements.txt
python collector.py
streamlit run app.py
```

## Cómo usarlo gratis en la nube con GitHub Actions

1. Creá un repositorio en GitHub.
2. Subí todos estos archivos.
3. Activá GitHub Actions.
4. El workflow `Collect Sim Companies market ticker` corre cada 6 minutos y también manualmente.
5. Guarda datos en `data/market_ticks.csv` y `data/product_phase_latest.csv`.

Recomendación: usá un repo público solo si no vas a guardar datos estratégicos personales. Para esta V0.1 solo guardamos precios públicos del mercado.

## Qué es una fase de mercado en esta app

La app usa el historial del precio de mercado, no el retail. Para cada producto/calidad calcula el percentil del último precio contra su historial.

- Percentil <= 20: barato / sobreoferta
- 20 a 40: bajo-normal
- 40 a 70: normal
- 70 a 90: caro
- > 90: pico / oportunidad de venta

También calcula una tendencia simple comparando media corta contra media larga.
