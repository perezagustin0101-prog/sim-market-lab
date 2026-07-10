Sim Market Lab V2.1 modular
===========================

Cambios principales respecto a V2:

1. Configuración global corregida:
   - Comisión de venta a mercado en porcentaje real: 4 = 4%.
   - Descuento por contrato en porcentaje real: 3 = 3%.
   - Se eliminó el multiplicador de salario.
   - Se eliminó la reducción admin suelta.
   - Se eliminó el transporte en contrato editable.
   - El transporte por contrato queda fijo en 50% del transporte de mercado, como regla del juego.

2. Bonificadores del juego:
   - Se reemplazó “multiplicador producción” por “Bono producción del juego (%)”.
   - Se agregó “Bono venta retail del juego (%)” para preparar módulos de retail.
   - Estos campos no representan una decisión inventada: son valores para copiar desde el juego.

3. Directores:
   - Nuevo apartado para cargar directores.
   - Campos: activo, nombre, puesto, Management, Accounting, Communication, Science, salario diario, reducción admin %, bono producción %, bono venta retail %.
   - El salario diario de directores se convierte a costo por hora y se descuenta del beneficio real.
   - La reducción admin y los bonos se cargan manualmente por ahora, hasta automatizar la fórmula exacta.

4. Fórmulas:
   - El beneficio real ahora incluye costo de directores/hora.
   - Los salarios de edificios ya no tienen multiplicador manual.
   - El admin overhead sigue estimado por niveles y puede reducirse con el campo de directores.

Uso:

1. Reemplazá el app.py anterior por este app.py.
2. Mantené tus CSV del repo: productos_v1.csv, edificios_v1.csv, historial_mercado.csv, configuracion_v1.json si existe.
3. Ejecutá:

streamlit run app.py
