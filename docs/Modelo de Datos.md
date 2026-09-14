Según la descripción de la entrega identifico entidades principales:

Local: id, nombre

Mesa: id, id_local, capacidad

EntradaCola: 
id, id_local, nombre_comensal, telefono_comensal, 
cantidad_personas, estado (esperando/llamado/sentado/no_show/cancelado),
orden, es_frecuente, id_mesa (nullable),
fecha_hora_union, fecha_hora_llamado (nullable)