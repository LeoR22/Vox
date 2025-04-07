# 🐦 Vox - Red Social en Microservicios (Clon de Twitter/X)
![Python](https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi) ![JWT](https://img.shields.io/badge/JWT-black?style=flat&logo=JSON%20web%20tokens) ![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=flat&logo=mongodb&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=flat&logo=react&logoColor=%2361DAFB) ![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?style=flat&logo=figma&logoColor=white) 

Vox es una red social inspirada en Twitter/X, construida con una arquitectura de **microservicios**, que permite escalar y mantener cada servicio de forma independiente. La solución está compuesta por servicios en **FastAPI**, usando bases de datos **MongoDB**, un **API Gateway** y una interfaz frontend en **React**.

---

## 🧱 Arquitectura del Proyecto

```bash
vox/
├── docker-compose.yml
├── api-gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       └── routes/
├── auth-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       └── services/
├── user-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       └── services/
├── post-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       └── services/
├── comment-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       └── services/
├── like-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       └── services/
├── friend-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── __init__.py
│       ├── config/
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       └── services/
└── chat-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py
    └── app/
        ├── __init__.py
        ├── config/
        ├── models/
        ├── schemas/
        ├── routes/
        └── services/
```
### 🧪 Tecnologías Usadas
🐍 FastAPI – Framework para construir APIs rápidas y eficientes

🐳 Docker & Docker Compose – Contenerización y orquestación

🍃 MongoDB – Base de datos NoSQL

⚛️ React – Frontend moderno y dinámico

🔐 JWT – Seguridad y autenticación basada en tokens

📡 Microservicios REST – Servicios desacoplados comunicándose vía HTTP

## 📥 Clonar y Descargar el Proyecto


### Clonar el proyecto

```
https://github.com/LeoR22/Vox.git
```

### Configuración el proyecto

Seleccionar el proyecto : Moverse al directorio principal

```
cd vox
```

## 🚀 Cómo ejecutar el proyecto

### Asegúrate de tener instalado:

Docker y Docker Compose

### Comando para levantar todo:

```
docker-compose up --build
```

### 🌐 Acceso a los servicios
**Servicio Puerto local Descripción**
- API Gateway 8000 Punto de entrada para las APIs
- Auth Service 8001 Registro y autenticación de usuarios
- User Service 8002 Gestión de perfiles de usuario
- Post Service 8003 Publicación de tuits
- Comment Service 8004 Comentarios en tuits
- Like Service 8008 Likes para tuits y comentarios
- Friend Service 8006 Sistema de seguimiento de usuarios
- Chat Service 8007 Mensajería privada entre usuarios
- MongoDB 27017 Base de datos NoSQL
- Frontend (React) 3000 Interfaz de usuario
- Por defecto, puedes acceder a la app web desde: <http://localhost:3000>

### ⚙️ Variables de entorno y configuración
En el archivo docker-compose.yml ya están configuradas las URLs entre servicios mediante nombres de contenedor y variables como:

```
.env
```

```
AUTH_SERVICE_URL=<http://auth-service:8001>
USER_SERVICE_URL=<http://user-service:8002>
POST_SERVICE_URL =<http://post-service:8003>
COMMENT_SERVICE_URL = <http://comment-service:8004>
LIKE_SERVICE_URL = <http://like-service:8008>
FRIEND_SERVICE_URL = <http://friend-service:8006>
CHAT_SERVICE_URL = <http://chat-service:8007>
```

Cada microservicio se conecta a su propia base de datos MongoDB alojada en el mismo contenedor (mongo).

### 📌 Ejemplos de endpoints
A través del API Gateway (<http://localhost:8000/docs>) puedes acceder a rutas como:

- POST /auth/register – Registro
- POST /auth/login – Login (retorna JWT)
- GET /users/me – Perfil actual
- POST /posts – Crear un tuit
- POST /comments/{post_id} – Comentar
- POST /likes/{post_id} – Like
- POST /follow/{user_id} – Seguir
- POST /chats – Enviar mensaje


## Contribuciones

**Si deseas contribuir a este proyecto, sigue estos pasos:**

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature-nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Agrega nueva funcionalidad'`).
4. Sube los cambios a la rama (`git push origin feature-nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

- Leandro Rivera: <leo.232rivera@gmail.com>
- Linkedin: <https://www.linkedin.com/in/leandrorivera/>

### ¡Feliz Codificación! 🚀

Si encuentras útil este proyecto, ¡dale una ⭐ en GitHub! 😊
