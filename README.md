# Sistema de control de flujo de efectivo para mueblerías

Aplicación bilingüe para registrar movimientos de efectivo y consultar el flujo del negocio. El sistema usa una API Flask con autenticación JWT y una interfaz React.

## Stack

- Frontend: React, Vite, Tailwind CSS, React Router y react-i18next.
- Backend: Python 3.13, Flask, Flask-SQLAlchemy y Flask-JWT-Extended.
- Desarrollo: SQLite. Producción: PostgreSQL mediante `DATABASE_URL`.

## Desarrollo local

Requiere Node.js/npm y Python 3.13. Desde la raíz, abre una terminal para cada servidor.

### Backend

```powershell
py -3.13 -m venv backend/.venv
& .\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
Copy-Item backend/.env.example backend/.env
& .\backend\.venv\Scripts\python.exe .\backend\seed_data.py
& .\backend\.venv\Scripts\python.exe .\backend\run.py
```

La API queda en `http://127.0.0.1:5000`. La primera ejecución crea SQLite, la empresa, el usuario dueño y las categorías de mueblería. Con los valores del `.env.example`, el acceso inicial es `dueno@muebleria.com` / `CambiarEsta123`; cambia esa contraseña antes de usar datos reales.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. Vite reenvía `/api` a `http://127.0.0.1:5000`; para otro host local, define `VITE_BACKEND_URL` antes de iniciar Vite. En producción, `VITE_API_URL` puede apuntar a la ruta pública de la API.

## Integración disponible

- `POST /api/auth/login` inicia sesión y devuelve el token y perfil.
- `GET /api/auth/perfil` restaura una sesión persistida.
- `GET /api/dashboard/resumen` entrega totales, actividad y datos por rol.
- `GET/POST /api/transacciones` lista y registra movimientos.
- `GET /api/categorias` carga las categorías de la empresa.
- `GET /api/salud` verifica el estado del backend.

El backend valida los permisos aunque el frontend oculte opciones: el cajero queda limitado a los movimientos del día y no recibe datos exclusivos del dueño.
