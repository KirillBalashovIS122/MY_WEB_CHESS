# NEIRO CHESS

Проект представляет собой платформу для шахматных игр с поддержкой различных режимов: игрок против игрока, игрок против ИИ и ИИ против ИИ. Проект состоит из бэкенда на FastAPI (Python), фронтенда на React и запускается через Docker.

---

## **Технологии**

- **Backend**: FastAPI (Python)
- **Frontend**: React, Vite
- **Инфраструктура**: Docker, Docker Compose

---

## **Запуск проекта**

### **1. Установка зависимостей**

Убедитесь, что у вас установлены следующие инструменты:

- **Docker** и **Docker Compose**
- **Git**

### **2. Клонирование репозитория**

```bash
git clone <https://github.com/KirillBalashovIS122/MY_WEB_CHESS.git>
cd MY_WEB_CHESS
```

### **3. Запуск через Docker Compose**

- Перейти в папку **docker**
```bash
cd docker
```
- Запустить проект
```bash
docker-compose up --build
```

- После запуска откройте браузер и перейдите по адресу
```bash
http://localhost:3000
```