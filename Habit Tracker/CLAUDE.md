---



## Regla 1 — Inspección obligatoria antes de modificar código

Antes de crear, editar o eliminar cualquier archivo:

1. Revisar la estructura actual del módulo afectado.
2. Verificar si ya existe funcionalidad similar en otra app.
3. Analizar imports, modelos, serializers, views y urls relacionadas.
4. Identificar convenciones ya usadas (nombres de variables, patrones de URL, estilos de respuesta API).
5. Explicar brevemente qué encontró antes de realizar cambios.

**Nunca asumir que una funcionalidad no existe sin verificar primero.**

Comandos útiles para inspección:
```bash
# Ver estructura del proyecto
find . -type f -name "*.py" | head -50

# Ver modelos existentes
grep -r "class.*Model" apps/

# Ver urls registradas
python manage.py show_urls
```

---

## Regla 2 — Verificación automática del estado del proyecto

Antes de implementar una nueva funcionalidad, verificar:

- Cómo está organizado actualmente el módulo involucrado.
- Dependencias relacionadas entre apps.
- Migraciones existentes (`python manage.py showmigrations`).
- Endpoints ya implementados.
- Si existen permisos, serializers o modelos reutilizables.

Si el proyecto tiene errores visibles (imports rotos, migraciones sin aplicar, conflictos),
advertirlos antes de continuar con la tarea.

---

## Regla 3 — Cambios grandes deben dividirse

Si una tarea implica más de un archivo o más de ~50 líneas de código nuevo:

1. Dividir en pasos pequeños y claros.
2. Explicar qué hará cada paso antes de ejecutarlo.
3. Implementar primero la base mínima funcional (no el caso ideal completo).
4. Esperar confirmación antes de continuar al siguiente paso si hay riesgo de romper algo.

Evitar generar cientos de líneas de código de una sola vez sin contexto.

---

## Regla 4 — Instalación de librerías

Antes de instalar cualquier dependencia nueva:

1. Explicar para qué sirve en el contexto de Nixi.
2. Justificar si realmente es necesaria o si ya existe algo equivalente.
3. Verificar si ya está en `requirements.txt`.
4. Verificar compatibilidad con Django 5.x y Python 3.12.

Librerías ya instaladas (no reinstalar):
- djangorestframework
- djangorestframework-simplejwt
- django-cors-headers
- psycopg2
- python-decouple (variables de entorno)

Nunca instalar paquetes redundantes o que dupliquen funcionalidad ya presente.

---

## Regla 5 — Optimización de tokens

Cuando se solicite cualquiera de lo siguiente:
- Documentación extensa
- Tutoriales o guías largas
- Reportes técnicos
- Análisis grandes de código
- Archivos de más de ~150 líneas

Primero preguntar:

> "¿Deseas que esto se genere como archivo Word o PDF para ahorrar tokens del chat?"

No generar archivos extensos automáticamente sin confirmación explícita del usuario.

---

## Regla 6 — Consistencia del proyecto

Todo código nuevo debe seguir:

- **Nombres de modelos:** PascalCase en español (ej: `PerfilMedico`, `DireccionEntrega`)
- **Nombres de campos:** snake_case en español (ej: `tipo_usuario`, `precio_consulta`)
- **Nombres de endpoints:** kebab-case en español (ej: `/api/auth/cambiar-contrasena/`)
- **Serializers:** nombrar como `[Entidad]Serializer` o `Actualizar[Entidad]Serializer`
- **Views:** nombrar como `[Accion]View` (ej: `RegistroView`, `LoginView`)
- **Permisos:** nombrar como `Es[Rol]` (ej: `EsMedico`, `EsPaciente`)
- **Respuestas API:** siempre usar `{"status": "success"|"error", "data": ..., "message": ...}`

No introducir nuevas arquitecturas, patrones o convenciones sin justificarlo explícitamente.

---

## Regla 7 — Validación antes de finalizar

Antes de dar cualquier tarea por completada, verificar:

- Imports correctos y sin referencias rotas.
- Sin errores de sintaxis obvios.
- Rutas registradas correctamente en `urls.py`.
- Coherencia entre modelo → serializer → view → url.
- Migraciones generadas si se modificaron modelos.

Siempre sugerir el comando para probar la funcionalidad recién implementada:

```bash
# Verificar que Django no tiene errores
python manage.py check

# Aplicar migraciones si hubo cambios en modelos
python manage.py makemigrations
python manage.py migrate

# Verificar endpoints registrados
python manage.py show_urls | grep <modulo>
```

---

## Regla 8 — Resumen de cambios

Después de cada modificación, entregar un resumen con:

| Campo | Detalle |
|---|---|
| Archivos modificados | lista de archivos tocados |
| Razón del cambio | por qué se hizo |
| Impacto posible | qué otras partes podrían verse afectadas |
| Siguiente paso | qué viene después |

---

## Regla 9 — Seguridad y buenas prácticas

Nunca:
- Hardcodear SECRET_KEY, contraseñas, tokens o credenciales en código.
- Exponer datos sensibles en logs.
- Guardar contraseñas en texto plano (siempre usar `set_password()`).
- Desactivar permisos o autenticación "temporalmente".
- Usar `DEBUG=True` en configuraciones de producción.
- Ignorar validaciones de COFEPRIS o LFPDPPP en módulos de salud.

Siempre:
- Leer secrets desde variables de entorno (`.env` + `python-decouple`).
- Usar `IsAuthenticated` como mínimo en endpoints que manejen datos del usuario.
- Agregar `RR02` (limitaciones del chatbot) en cualquier vista del módulo chatbot.
- Cifrar datos sensibles de salud en reposo (requisito RR03 del proyecto).

---

## Regla 10 — Modo análisis antes de actuar

Para cualquier solicitud que implique cambios en el sistema:

1. **Analizar** → revisar archivos y módulos relacionados.
2. **Planificar** → explicar en 3-5 líneas qué se va a hacer y por qué.
3. **Advertir** → señalar riesgos, dependencias o posibles conflictos.
4. **Ejecutar** → implementar el cambio.
5. **Validar** → confirmar que no hay errores y sugerir pruebas.

No saltar directamente al paso 4 sin pasar por los anteriores.

---

## Estado actual del proyecto (referencia rápida)

### Fase 3 — Sistema de Autenticación

| Bloque | Descripción | Estado |
|--------|-------------|--------|
| Bloque 1 | CustomUser con roles + modelos de soporte | ✅ Completo |
| Bloque 2 | DRF + Simple JWT + CORS instalados y configurados | ✅ Completo |
| Bloque 3 | Perfiles por rol (PerfilCliente, PerfilMedico, PerfilFarmaceutico) | ✅ Completo |
| Bloque 4 | Serializers de usuario (registro, login, perfil, cambio de contraseña) | ✅ Completo |
| Bloque 5 | Views y endpoints de autenticación | ⏳ Pendiente |
| Bloque 6 | Permisos personalizados por rol | ⏳ Pendiente |
| Bloque 7 | Pruebas con Postman / Thunder Client | ⏳ Pendiente |

**Próximo paso:** Bloque 5 — Views / Endpoints de Autenticación.

---

## Requisitos MUST del MVP (referencia para priorización)

Estos requisitos son innegociables para el MVP según el levantamiento con 309 usuarios y 6 médicos:

- RF01: Solicitud de medicamentos por múltiples vías
- RF02: Métodos de pago (efectivo, transferencia, tarjeta)
- RF12: Registro de alergias del usuario
- RF15: Seguimiento de entrega en tiempo real
- RNF02: Operación con conectividad limitada (offline-first)
- RNF03: Accesibilidad WCAG 2.1 AA
- RR02: El chatbot NUNCA emite diagnósticos médicos
- RR03: Datos de salud cifrados (LFPDPPP)
- D-01: Configuración de agenda médica con tope de citas
- D-08: El agente IA siempre aclara que no es médico
- D-11: Reconexión en teleconsulta en menos de 60 segundos
- D-12: Responsabilidad clínica documentada en interfaz

---

---

## Regla 11 — Resumen automático antes de alcanzar límite de contexto

Cuando la conversación alcance aproximadamente el 90% del límite de contexto o tokens disponibles:

1. Detener temporalmente nuevas implementaciones grandes.
2. Generar automáticamente un resumen técnico estructurado del estado actual del proyecto.
3. El resumen debe incluir:

### Estado general
- Qué fase del proyecto está activa.
- Qué módulos fueron trabajados.
- Qué funcionalidades ya están completas.
- Qué funcionalidades siguen pendientes.

### Cambios realizados durante la sesión
- Archivos creados.
- Archivos modificados.
- Migraciones generadas.
- Endpoints agregados.
- Modelos/serializers/views/permisos implementados.
- Dependencias instaladas.

### Estado técnico actual
- Errores detectados pendientes.
- Problemas conocidos.
- Riesgos o deuda técnica.
- Validaciones faltantes.
- Partes no terminadas.

### Próximos pasos recomendados
- Qué bloque sigue.
- Qué archivos deberían modificarse después.
- Qué pruebas faltan.
- Qué endpoints deben validarse.

### Formato obligatorio del resumen

El resumen debe estar estructurado así:

```md
# RESUMEN DE SESIÓN — PROYECTO NIXI

## ✅ Completado
- ...

## ⏳ Pendiente
- ...

## 📁 Archivos modificados
- ...

## ⚠ Problemas detectados
- ...

## ▶ Próximo paso recomendado
- ...
---

## Regla 13 — Sugerencia automática de commits

Después de realizar cambios importantes o estables en el proyecto, evaluar automáticamente si es un buen momento para generar un commit de Git.

Considerar como "cambio importante" cualquiera de los siguientes casos:

- Creación de nuevos modelos.
- Implementación completa de un endpoint.
- Finalización de un bloque funcional.
- Cambios en migraciones.
- Implementación de autenticación o permisos.
- Refactorización grande.
- Cambios en múltiples archivos relacionados.
- Corrección de errores críticos.
- Configuración importante del proyecto.
- Integración de librerías o servicios nuevos.

Si se cumple alguno de esos casos:

1. Informar al usuario que el estado actual ya es suficientemente estable para un commit.
2. Explicar brevemente qué quedó funcional.
3. Sugerir un mensaje de commit profesional siguiendo Conventional Commits.


Regla 14 — No generar documentos en el chat

Nunca generar automáticamente:

Canvas
Documentos Word
PDFs
Bloques de documento extensos
Archivos largos incrustados en el chat

Toda respuesta debe mantenerse en formato texto plano (txt) dentro del chat, salvo que el usuario solicite explícitamente otro formato.

Evitar respuestas excesivamente largas o decoradas visualmente.

Regla 15 — Manejo de resúmenes y contexto continuo

Cuando el usuario proporcione un nuevo resumen del proyecto, estado técnico o contexto:

Leer completamente el resumen.
Usarlo como contexto activo para las siguientes respuestas.
No reestructurar ni reinterpretar innecesariamente el resumen.
No generar análisis extensos automáticamente.
No repetir el contenido completo del resumen.
Continuar directamente desde el estado descrito por el usuario.

El objetivo es:

mantener continuidad del proyecto,
reducir consumo de tokens,
evitar respuestas redundantes,
seguir trabajando desde el último estado conocido.

Si el resumen incluye:

tareas pendientes,
errores,
módulos activos,
decisiones técnicas,
convenciones,
arquitectura,

entonces asumirlas como válidas para las siguientes respuestas hasta que el usuario indique cambios.
