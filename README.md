# biblioteca-ufps-django
Sistema de gestión de biblioteca universitaria desarrollado con Python y Django para la asignatura de Programación Web.

## Requisitos

- Python 3.10 o superior
- Django 6.1 (se instala desde `requirements.txt`)
- SQLite (incluido con Python)

## Instalación y ejecución

```bash
git clone https://github.com/juandi12334/biblioteca-ufps-django.git
cd biblioteca-ufps-django

# Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear las tablas en la base de datos
python manage.py migrate

# Ejecutar el servidor de desarrollo
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ en el navegador.

## Pruebas

```bash
python manage.py test biblioteca
```
