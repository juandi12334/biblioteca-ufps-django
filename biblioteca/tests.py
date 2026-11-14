from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Autor, Categoria, Ejemplar, Estudiante, Libro, Prestamo


class PrestamoActivoUnicoTest(TestCase):
    """Comprueba la regla: una copia no puede estar prestada a dos personas a la vez."""

    def setUp(self):
        categoria = Categoria.objects.create(nombre="Ingeniería")
        autor = Autor.objects.create(nombre="Andrew S. Tanenbaum")
        libro = Libro.objects.create(
            titulo="Organización de computadoras",
            anio_publicacion=2006,
            isbn="9789702608172",
            categoria=categoria,
        )
        libro.autores.add(autor)
        self.ejemplar = Ejemplar.objects.create(codigo_inventario="INV-001", libro=libro)
        self.otro_ejemplar = Ejemplar.objects.create(codigo_inventario="INV-002", libro=libro)
        self.ana = Estudiante.objects.create(
            codigo="1152001", nombre="Ana Pérez", correo="ana@ufps.edu.co"
        )
        self.luis = Estudiante.objects.create(
            codigo="1152002", nombre="Luis Gómez", correo="luis@ufps.edu.co"
        )

    def prestar(self, ejemplar, estudiante):
        return Prestamo.objects.create(
            ejemplar=ejemplar,
            estudiante=estudiante,
            fecha_salida=date(2026, 11, 3),
            fecha_limite=date(2026, 11, 17),
        )

    def test_no_se_puede_prestar_dos_veces_la_misma_copia(self):
        self.prestar(self.ejemplar, self.ana)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.prestar(self.ejemplar, self.luis)

    def test_se_puede_prestar_de_nuevo_despues_de_devolver(self):
        prestamo = self.prestar(self.ejemplar, self.ana)
        prestamo.fecha_devolucion = date(2026, 11, 10)
        prestamo.save()
        self.prestar(self.ejemplar, self.luis)
        self.assertEqual(Prestamo.objects.filter(ejemplar=self.ejemplar).count(), 2)

    def test_copias_distintas_se_pueden_prestar_al_mismo_tiempo(self):
        self.prestar(self.ejemplar, self.ana)
        self.prestar(self.otro_ejemplar, self.luis)
        self.assertEqual(Prestamo.objects.filter(fecha_devolucion__isnull=True).count(), 2)
