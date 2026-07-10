Sim Market Lab V2 - Business Simulator

Qué incluye:
- app.py nuevo con una sola pantalla modular.
- Módulos: configuración global, escenarios, edificios, recetas, fuentes de insumos, mercado, beneficio, sobrantes/faltantes, costos y comparador.
- Usa los CSV existentes del repo: productos_v1.csv, edificios_v1.csv, historial_mercado.csv y configuracion_v1.json si existen.

Cómo instalar en el repo actual:
1) Hacé una copia de seguridad de tu app.py actual.
2) Pegá este app.py en la raíz del repo sim-market-lab, reemplazando el anterior.
3) En la terminal:
   pip install -r requirements.txt
   streamlit run app.py

Notas:
- No toca tu cuenta de Sim Companies.
- No usa login ni cookies.
- El comparador calcula, no recomienda.
- El capital base aproximado todavía NO es upgrade exacto; usa costo N1 x niveles como proxy simple.
