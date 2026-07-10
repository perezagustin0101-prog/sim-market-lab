Sim Market Lab V2.2 modular
===========================

Cambios principales de V2.2:

1) Separación base vs efectivo
- productos_v1.csv y edificios_v1.csv deben guardar valores base puros del juego, sin bonus.
- Las bonificaciones de cuenta/HQ y directores se cargan aparte.
- La app muestra una tabla de control: Producción base/h vs Producción efectiva/h.

2) Bonificaciones de cuenta / HQ
- Bonus producción cuenta/HQ (%) se carga como porcentaje real: 3 significa 3%.
- Bonus venta retail cuenta/HQ (%) queda separado para retail.
- La app muestra el multiplicador aplicado.

3) Directores
- Se mantienen directores con salario diario y efectos manuales.
- El salario diario activo se descuenta por hora del beneficio.
- La reducción admin y bonos de directores se suman a las bonificaciones globales.

4) Costos y simulación
- Los cálculos usan valores base del CSV y luego aplican bonus.
- En ventas aparece Producción base/h y Producción efectiva/h.
- Esto evita mezclar datos base con datos ya bonificados.

Uso:
1. Reemplazar app.py del repo por este app.py.
2. Mantener productos_v1.csv, edificios_v1.csv, historial_mercado.csv y configuracion_v1.json en el repo.
3. Ejecutar:
   streamlit run app.py

Nota:
Si la columna Producción base/h ya coincide con lo que el juego te muestra después de aplicar bonus, entonces el CSV está cargado con valores bonificados y hay que corregirlo para evitar doble conteo.
