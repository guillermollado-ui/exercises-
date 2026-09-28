# CLAUDE.md — Reglas de trabajo

> Reglas de proceso generales. Complementan (no sustituyen) las reglas técnicas
> propias de cada proyecto, que deben vivir en su propio CLAUDE.md.

## Flujo de trabajo
1. Antes de escribir código, propone un plan: archivos a tocar, funciones
   concretas, orden de operaciones. Espera aprobación explícita antes de
   implementar.
2. Si durante la implementación algo se desvía del plan aprobado (un archivo
   extra, un cambio no previsto, una complicación), **párate y repórtalo**.
   No improvises fuera del plan.
3. Mantén intervención mínima: no añadas refactors, abstracciones ni
   funcionalidades que no se hayan pedido. Tres líneas repetidas son mejor
   que una abstracción prematura.
4. Verifica cada cambio (tests, lint, build o ejecución manual según
   aplique) antes de darlo por terminado. No afirmes que algo funciona sin
   haberlo comprobado.
5. Pasa el subagente `revisor` antes de dar un cambio por terminado o listo
   para mergear.
6. Antes de cada commit, revisa `git diff` / `git status` completo. No
   commitees ni hagas push salvo petición explícita en ese momento.
7. Al entregar un archivo modificado, entrégalo completo, nunca fragmentos
   ni "...resto igual...".

## Seguridad
- Nunca subas ni expongas claves, tokens, contraseñas o archivos `.env` en
  código, commits o mensajes.
- Antes de un `git add` amplio, revisa qué se ha incluido; si algo parece
  sensible aunque el nombre del archivo no lo sugiera, comprueba su
  contenido antes de continuar.

## Acciones de riesgo
- Para operaciones destructivas o difíciles de revertir (borrar archivos,
  `git reset --hard`, `push --force`, cambiar variables de entorno,
  migraciones de esquema, tocar flujos de pago o autenticación), pide
  confirmación explícita antes de actuar, salvo instrucción previa que lo
  autorice para ese caso concreto.
