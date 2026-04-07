Requisitos previos (instalar una sola vez)

  - Python 3.11+
  - Node.js 18+
  - Flutter SDK
  - PostgreSQL
  - Android Studio + emulador configurado

  ---
  1. Clonar el repositorio

  git clone <url-del-repo>

  ---
  2. Backend

  cd taller_backend

  # Crear y activar entorno virtual
  python -m venv venv
  .\venv\Scripts\activate       # Windows

  # Instalar dependencias
  pip install -r requirements.txt
  pip install bcrypt==4.0.1     # versión compatible con passlib

  # Crear el archivo .env (no está en el repo)

  Crear manualmente el archivo taller_backend/.env:
  DATABASE_URL=postgresql+asyncpg://postgres:12345678@localhost:5432/tall  er
  SECRET_KEY=cambia_esta_clave_secreta
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30

  # Crear la base de datos en PostgreSQL
  psql -U postgres -c "CREATE DATABASE taller;"

  # Cargar usuarios de prueba
  python seed.py

  # Levantar el servidor
  py run.py

  ---
  3. Web

  cd taller_web
  npm install
  npm start
  # Abre http://localhost:4200

  ---
  4. Móvil

  cd taller_movil
  flutter pub get
  # Tener un emulador Android corriendo
  flutter run

  ---
  Credenciales de prueba

  ┌────────────────────┬────────────┬─────────┐
  │       Email        │ Contraseña │   Rol   │
  ├────────────────────┼────────────┼─────────┤
  │ admin@taller.com   │ 12345678   │ Admin   │
  ├────────────────────┼────────────┼─────────┤
  │ cliente@taller.com │ 12345678   │ Cliente │
  ├────────────────────┼────────────┼─────────┤
  │ taller@taller.com  │ 12345678   │ Taller  │
  └────────────────────┴────────────┴─────────┘

  ▎ Importante: el .env nunca se sube al repo. Cada integrante debe
  crearlo manualmente con sus propias credenciales de PostgreSQL.
