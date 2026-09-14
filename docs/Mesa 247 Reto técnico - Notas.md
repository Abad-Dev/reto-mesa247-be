
> [!NOTE] Mensaje del diseñador
> 
> ¡Hola! Te paso esto. Los restaurantes con mucho walk-in tienen los viernes colas de 30 a 40 personas en la puerta, anotadas en un cuaderno. Se pierden nombres, la gente se va sin avisar y el anfitrión no da abasto. Queremos una lista de espera digital:
> 
> 1. El comensal escanea un QR en la puerta, pone su nombre, su teléfono y cuántos son, y entra a la cola.
> 2. En su celular ve su posición en vivo —que baja con una animación cuando avanza la cola— y un tiempo estimado de espera.
> 3. Cuando su mesa está lista le llega un WhatsApp con dos botones: «Voy en camino» y «Ya no voy».
> 4. El anfitrión ve la cola en su tablet, puede arrastrar para reordenar (a veces priorizan a un cliente frecuente) y toca «Llamar».
> 5. Al cierre del día, un reporte: cuánta gente se fue sin sentarse.
> 
> Te adjunto el prototipo, son cinco pantallas. Es para un piloto con tres locales —La Terraza Azul y Cuatro Vientos en Lima, y Casa Mediterránea en Santiago— en tres semanas. ¿Qué necesitas?
> 
## Huecos que identifico:
1. Relación con **"El Libro"**: Los restaurantes actualmente usan un sistema escrito en PHP, donde tienen sus mesas y reservas. Para la creación de este sistema sería necesario hacer una migración para que se pueda reutilizar la base de datos que tienen. De lo contrario, los restaurantes tendrán que agregar sus mesas y locales. 
2. Cálculo del tiempo estimado: Es un dato autocalculado en base a la lista de espera o es ingresado manualmente por el anfitrión?
3. Identidad del anfitrión: Actualmente una misma tablet la usan 2 anfitriones y actualmente tienen que pasar por un login. Es necesario identificar quien realiza que acciones en la tablet? De ser así se puede implementar una identificación por código o un dropdown select para identificarlos, más fácil que pasar por 4 pantallas solo para decidir quien realizó qué reserva.
4. Timeout del "tienes 10 minutos": Que pasará cuando un cliente no llegue dentro de los 10 minutos? Se le descartará automáticamente o se descartará de forma manual por los anfitriones
## Lo que queda fuera de alcance:
1. Integración Real con WhatsApp Business: Es una dependencia externa, es un riesgo depender del tiempo de Meta para esta integración. Este proceso requiere aprobación de plantillas, tarifa por país, proveedor SMS aparte, etc. Queda diseñada en el flujo, pero la notificación real la resuelve la pantalla 2.
2. Reporte del día: No es el corazón del producto, se puede obtener de la data que se tendrá en la tabla de cola. Es fácilmente implementable con un query manual o un cron simple, debido al poco tiempo no vale la pena construirla ahora.
3. Detección automática de cliente frecuente: Hoy en día es 100% criterio humano del anfitrión, automatizarlo es una feature nueva que requiere procesos de briefing, coordinación con el equipo y además depende de cada restaurante, no es una migración de lo existente. Queda documentado como upsell para una Phase 2.
4. Integración real con "El Libro": No va a ser posible tener acceso al libro en 4 horas. La capacidad de las mesas, la cantidad de mesas, los locales, etc queda como data seedeada y con una posibilidad de migración de los datos existentes.
5. No se guardará un historial sobre sus clientes y sus visitas ya que no entra en el alcance de las 4 horas y no es necesario dado que la identificación de "cliente frecuente" ya se resolvió como un criterio manual del anfitrión.

## Preguntas para el diseñador:
1. ¿Cómo se calcula el tiempo estimado de espera?
2. ¿Qué pasa si el comensal no llega dentro de los 10 minutos tras ser llamado?
3. ¿Es posible acceder a la base de datos de El Libro para hacer una migración de los datos?

## Assumptions:
- La capacidad de las mesas se resuelve leyendo la data que existe en "El Libro" (o después que llenen la información si es que no se puede recuperar esa data).
- Los clientes frecuentes por ahora será el criterio manual del anfitrión (como lo hacen hoy). Se documenta como riesgo de conocimiento no estandarizado y se propone como feature para un upsell.
- No se permitirá a un usuario unirse dos veces a la cola (se identificará por nombre, ya que el teléfono puede compartirse entre acompañantes que anotan por otro).
- No se identificará individualmente al anfitrión que ejecuta cada acción en el piloto. Ambos operan sobre la misma sesión de tablet sin login. Se propone un selector simple (dropdown) como mejora de trazabilidad si se prioriza en una fase posterior.
- Se integrará polling (por la conexión deficiente, no es víable usar websockets ya que se rompe la conexión) para mantener la data actualizada en tiempo real en la cola y en la vista del comensal (esto reemplaza la notificación de "Mesa Lista" sin WhatsApp)
- El timeout de los 10 minutos se resuelve de forma manual por el anfitrión, un comensal puede llegar unos segundos después del límite y perder su lugar, o el anfitrión puede haberse olvidado de marcar que llegó y se perdió la reserva injustamente. Por ahora se deja en manos del anfitrión ya que está en la puerta viendo a los comensales, es más seguro para el piloto y no implica bloqueantes (Incluso se puede automatizar después).