# biblioteca-ufps-django

Sistema de gestión de biblioteca universitaria desarrollado con Python y Django para la asignatura de Programación Web.

## Requisitos e instalación

Python 3.10 o superior, Django 6.1.3 y SQLite.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_datos_demo
python manage.py createsuperuser
python manage.py runserver
```

Abrir http://127.0.0.1:8000/. `cargar_datos_demo` crea/actualiza un conjunto repetible de 5 libros, 3 autores, 8 ejemplares, 4 estudiantes y 6 préstamos (3 devueltos, 3 activos). Los retos 1 y 10 añaden y borran un libro/autor de práctica.

## Fase 5: Consultas ORM

Ejecutar con `python manage.py shell`, después de cargar los datos demo. Importaciones:

```python
from datetime import date
from django.db.models import Count, Exists, OuterRef
from biblioteca.models import Autor, Categoria, Ejemplar, Estudiante, Libro, Prestamo
```

Los resultados fueron observados en una base nueva, con los retos ejecutados en orden. Antes de cada consulta se anota la predicción.

### 1. Crear autor, libro y dos copias

**Predicción:** crea un autor, un libro asociado y dos ejemplares.

```python
categoria = Categoria.objects.get(nombre="Tecnología")
autor, _ = Autor.objects.get_or_create(nombre="Autor de práctica ORM")
libro, _ = Libro.objects.get_or_create(isbn="9780000000099", defaults={"titulo": "Práctica ORM especial", "anio_publicacion": 2026, "categoria": categoria})
libro.autores.add(autor)
for numero in (1, 2):
    Ejemplar.objects.get_or_create(codigo_inventario=f"ORM-RET0{numero}", defaults={"libro": libro})
list(libro.ejemplar_set.values_list("codigo_inventario", flat=True))
```

**Resultado:** `['ORM-RET01', 'ORM-RET02']`.

### 2. Libros de un autor buscado por nombre

**Predicción:** devuelve los libros asociados a Ada Lovelace.

```python
list(Libro.objects.filter(autores__nombre="Ada Lovelace").order_by("titulo").values_list("titulo", flat=True))
```

**Resultado:** `['Algoritmos y estructuras', 'Introducción a Python']`.

### 3. Título que contiene una palabra sin distinguir mayúsculas

**Predicción:** `icontains` encuentra el título aunque la búsqueda esté en mayúsculas.

```python
list(Libro.objects.filter(titulo__icontains="ALGORITMOS").values_list("titulo", flat=True))
```

**Resultado:** `['Algoritmos y estructuras']`.

### 4. Ejemplares disponibles

**Predicción:** devuelve ejemplares sin préstamo activo (`fecha_devolucion` nula).

```python
prestamo_activo = Prestamo.objects.filter(ejemplar=OuterRef("pk"), fecha_devolucion__isnull=True)
list(Ejemplar.objects.annotate(tiene_activo=Exists(prestamo_activo)).filter(tiene_activo=False).order_by("codigo_inventario").values_list("codigo_inventario", flat=True))
```

**Resultado:** `['DEMO-0001-1', 'DEMO-0001-2', 'DEMO-0004-2', 'DEMO-0005-1', 'ORM-RET01', 'ORM-RET02']`.

### 5. Estudiantes con préstamo activo, sin repetir

**Predicción:** Ana, Luis y María; cada estudiante aparece una sola vez.

```python
prestamo_activo = Prestamo.objects.filter(estudiante=OuterRef("pk"), fecha_devolucion__isnull=True)
list(Estudiante.objects.annotate(tiene_activo=Exists(prestamo_activo)).filter(tiene_activo=True).order_by("codigo").values_list("nombre", flat=True))
```

**Resultado:** `['Ana Pérez', 'Luis Gómez', 'María Rojas']`.

### 6. Contar todos los préstamos por estudiante

**Predicción:** cuenta activos y devueltos; Carlos aparecerá con cero.

```python
list(Estudiante.objects.annotate(total=Count("prestamo")).order_by("codigo").values_list("nombre", "total"))
```

**Resultado:** `[('Ana Pérez', 2), ('Luis Gómez', 2), ('María Rojas', 2), ('Carlos Díaz', 0)]`.

### 7. Libro más prestado

**Predicción:** el conteo cruza desde libro a ejemplares y préstamos; gana Algoritmos y estructuras.

```python
list(Libro.objects.annotate(total=Count("ejemplar__prestamo")).order_by("-total", "titulo").values_list("titulo", "total")[:1])
```

**Resultado:** `[('Algoritmos y estructuras', 2)]`.

### 8. Estudiantes que nunca han pedido préstamos

**Predicción:** solo Carlos Díaz no tiene préstamos.

```python
list(Estudiante.objects.filter(prestamo__isnull=True).order_by("codigo").values_list("nombre", flat=True))
```

**Resultado:** `['Carlos Díaz']`.

### 9. Marcar un préstamo como devuelto y comprobar el guardado

**Predicción:** guarda la fecha de hoy para el préstamo activo de esa copia.

```python
prestamo = Prestamo.objects.get(ejemplar__codigo_inventario="DEMO-0002-1")
prestamo.fecha_devolucion = date.today()
prestamo.save()
prestamo.refresh_from_db()
prestamo.fecha_devolucion
```

**Resultado observado al ejecutar:** `2026-11-21`. Para restaurar el conjunto de medición: `prestamo.fecha_devolucion = None; prestamo.save()`.

### 10. Borrar un autor y observar sus libros

**Predicción:** el libro permanece, porque el autor está relacionado mediante `ManyToManyField`; se borra la asociación.

```python
libro = Libro.objects.get(isbn="9780000000099")
autor = Autor.objects.get(nombre="Autor de práctica ORM")
Libro.objects.filter(pk=libro.pk).exists()  # True antes
autor.delete()
Libro.objects.filter(pk=libro.pk).exists()  # True después
```

**Resultado:** `True` antes y `True` después. La tabla intermedia elimina la asociación. No hay `on_delete` entre libro y autor porque no es un `ForeignKey`.

## Fase 6: Optimización N+1

El patrón N+1 consulta la lista y luego hace consultas adicionales al acceder en un bucle a relaciones no cargadas. Se midió con `CaptureQueriesContext`; se recorren los campos relacionados dentro del bloque para que las consultas se ejecuten durante la captura.

### Préstamos, estudiante y libro de la copia

**Predicción:** con 6 préstamos, la consulta inicial y hasta 3 consultas por préstamo (estudiante, ejemplar y libro) suman 19. `select_related` puede unir esas `ForeignKey` en una consulta.

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as consultas:
    for prestamo in Prestamo.objects.all():
        print(prestamo.estudiante.nombre, prestamo.ejemplar.libro.titulo)
print(len(consultas))

with CaptureQueriesContext(connection) as consultas:
    for prestamo in Prestamo.objects.select_related("estudiante", "ejemplar__libro"):
        print(prestamo.estudiante.nombre, prestamo.ejemplar.libro.titulo)
print(len(consultas))
```

### Libros y autores

**Predicción:** 6 libros provocan 7 consultas (una lista y una por libro); `prefetch_related` reduce el total a dos.

```python
with CaptureQueriesContext(connection) as consultas:
    for libro in Libro.objects.all():
        print(libro.titulo, [autor.nombre for autor in libro.autores.all()])
print(len(consultas))

with CaptureQueriesContext(connection) as consultas:
    for libro in Libro.objects.prefetch_related("autores"):
        print(libro.titulo, [autor.nombre for autor in libro.autores.all()])
print(len(consultas))
```

`select_related` no se aplica a autores porque `Libro.autores` es muchos a muchos y puede devolver varios objetos por libro. `select_related` sigue relaciones a un objeto (`ForeignKey`/`OneToOneField`); `prefetch_related` carga las relaciones múltiples en una consulta aparte y las asocia en memoria.

Medición observada con SQLite, 6 préstamos y 6 libros (incluido el libro añadido en el reto 1):

| Consulta | Número de consultas antes | Número de consultas después |
|---|---:|---:|
| Préstamos con estudiante y libro del ejemplar (`select_related`) | 19 | 1 |
| Libros con autores (`prefetch_related`) | 7 | 2 |

Los conteos corresponden a este conjunto de datos y al recorrido descrito; pueden cambiar si varía el número de registros.

## Pruebas

```bash
python manage.py test biblioteca
```
