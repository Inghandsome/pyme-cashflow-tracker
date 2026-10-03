"""Punto de entrada del backend.

Desarrollo::

    python run.py

Producción (Docker / Render)::

    gunicorn run:app
"""

from app import crear_app

app = crear_app()

if __name__ == "__main__":
    # 127.0.0.1 por seguridad: para exponerlo en la red local, cambia a 0.0.0.0
    app.run(host="127.0.0.1", port=5000, debug=True)
