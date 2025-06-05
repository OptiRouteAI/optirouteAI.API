# Backend - Sistema de Optimización de Picking

Este backend está desarrollado con **FastAPI** y sigue una arquitectura modular basada en **Domain-Driven Design (DDD)**. Su objetivo principal es gestionar operaciones logísticas en un almacén, incluyendo pedidos, picking y manejo de stock.

## 🧱 Tecnologías principales
- **FastAPI** – Framework web moderno y rápido.
- **SQLAlchemy ORM** – Mapeo objeto-relacional para base de datos.
- **MySQL** – Motor de base de datos relacional.
- **Pydantic** – Validación y serialización de datos.
- **Alembic** (opcional) – Migraciones de esquemas de base de datos.

---

# 📦 Módulo Picking Tradicional

Este módulo permite generar y gestionar el proceso de picking de forma tradicional, seleccionando los pedidos y reservando stock automáticamente desde las ubicaciones disponibles.

## ⚙️ Funcionalidades principales

- 🔁 **Generar Picking**: a partir de uno o más pedidos seleccionados.
- 📄 **Listar Pickings**: vista de cabecera para mostrar número, estado y fecha.
- 🔍 **Detalle de Picking**: información detallada del pedido, cliente, artículos y ubicaciones.

---

