from datetime import date, timedelta

from django.core.management.base import BaseCommand

from biblioteca.models import Autor, Categoria, Ejemplar, Estudiante, Libro, Prestamo


class Command(BaseCommand):
    help = "Crea o actualiza datos de ejemplo para practicar consultas ORM."

    def handle(self, *args, **options):
        tecnologia, _ = Categoria.objects.get_or_create(nombre="Tecnología")
        ciencias, _ = Categoria.objects.get_or_create(nombre="Ciencias")
        humanidades, _ = Categoria.objects.get_or_create(nombre="Humanidades")

        autores = {}
        for nombre in ("Ada Lovelace", "Alan Turing", "Grace Hopper"):
            autores[nombre], _ = Autor.objects.get_or_create(nombre=nombre)

        catalogo = [
            ("Algoritmos y estructuras", 2020, "9780000000001", tecnologia, ["Ada Lovelace", "Alan Turing"], 2),
            ("Computación moderna", 2019, "9780000000002", tecnologia, ["Alan Turing"], 2),
            ("Historia de la ciencia", 2018, "9780000000003", humanidades, ["Grace Hopper"], 1),
            ("Introducción a Python", 2022, "9780000000004", tecnologia, ["Ada Lovelace"], 2),
            ("Fundamentos de lógica", 2021, "9780000000005", ciencias, ["Grace Hopper", "Alan Turing"], 1),
        ]
        ejemplares = []
        for titulo, anio, isbn, categoria, nombres, cantidad in catalogo:
            libro, _ = Libro.objects.update_or_create(
                isbn=isbn,
                defaults={"titulo": titulo, "anio_publicacion": anio, "categoria": categoria, "idioma": "Español"},
            )
            libro.autores.set(autores[nombre] for nombre in nombres)
            for numero in range(1, cantidad + 1):
                ejemplar, _ = Ejemplar.objects.get_or_create(
                    codigo_inventario=f"DEMO-{isbn[-4:]}-{numero}",
                    defaults={"libro": libro, "condicion": "nuevo"},
                )
                ejemplares.append(ejemplar)

        estudiantes = []
        for codigo, nombre in (
            ("DEMO-001", "Ana Pérez"),
            ("DEMO-002", "Luis Gómez"),
            ("DEMO-003", "María Rojas"),
            ("DEMO-004", "Carlos Díaz"),
        ):
            estudiante, _ = Estudiante.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": nombre, "correo": f"{codigo.lower()}@ufps.edu.co"},
            )
            estudiantes.append(estudiante)

        hoy = date.today()
        prestamos = [
            (0, 0, hoy - timedelta(days=30), hoy - timedelta(days=16)),
            (1, 1, hoy - timedelta(days=25), hoy - timedelta(days=11)),
            (2, 2, hoy - timedelta(days=20), hoy - timedelta(days=6)),
            (3, 0, hoy - timedelta(days=5), hoy + timedelta(days=9)),
            (4, 1, hoy - timedelta(days=3), hoy + timedelta(days=11)),
            (5, 2, hoy - timedelta(days=1), hoy + timedelta(days=13)),
        ]
        for index, (ejemplar_index, estudiante_index, salida, limite) in enumerate(prestamos, 1):
            devuelto = salida + timedelta(days=7) if index <= 3 else None
            Prestamo.objects.update_or_create(
                ejemplar=ejemplares[ejemplar_index],
                estudiante=estudiantes[estudiante_index],
                fecha_salida=salida,
                defaults={"fecha_limite": limite, "fecha_devolucion": devuelto},
            )

        self.stdout.write(self.style.SUCCESS("Datos demo disponibles: 5 libros, 3 autores, 8 ejemplares, 4 estudiantes y 6 préstamos."))
