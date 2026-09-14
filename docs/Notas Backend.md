Endpoints básicos:

1. Comensal envía nueva entrada a la cola - POST /cola
2. Comensal ve su puesto en la cola (polling) - GET /cola/:id
3. Anfitrión ve la cola completa - GET /cola?local_id=X
4. Anfitrión actualiza el tiempo estimado del comensal en la cola - PATCH /cola/:id
5. Anfitrión reordena los comensales en la cola - PUT /cola/:id/reordenar
6. Anfitrión llama al comensal en la cola - PATCH /cola/:id/llamar
7. Anfitrión sienta al comensal en la mesa - PATCH /cola/:id/sentar

