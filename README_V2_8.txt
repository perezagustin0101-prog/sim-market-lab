Sim Market Lab V2.8

Cambios principales:
- Se eliminó la columna Perfil de Directores.
- Ahora queda una sola columna Puesto: COO, CFO, CMO, CTO o Staff.
- La búsqueda de “COO/CFO/CMO/CTO” se representa con los puntos del director: Gestión, Contabilidad, Comunicación y Ciencia.
- Mejora contable ahora se muestra en dinero completo ($), no en $M, para evitar diferencias visuales como 0,3M arriba y 0,2M abajo.
- La mejora contable NO es beneficio directo; representa el efecto estimado de Contabilidad sobre el umbral/cargo contable.
- Se mantiene el cálculo cruzado por puesto: el puesto principal pesa completo y los demás aportan parcialmente. Es un modelo provisional hasta calibrarlo con lo que muestra el juego.

Uso:
Reemplazar app.py en el repo y correr:
streamlit run app.py
