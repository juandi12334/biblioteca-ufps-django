from django.db import models
from django.db.models import Q

# Diseño a partir del enunciado:
# - Entidades: Categoria, Autor, Libro, Ejemplar (copia física), Estudiante, Prestamo.
# - Relaciones:
#   * Categoria 1 - N Libro       (cada libro pertenece a una categoría)
#   * Libro N - N Autor           (un libro tiene varios autores y un autor varios libros)
#   * Libro 1 - N Ejemplar        (un libro puede tener varias copias físicas)
#   * Ejemplar 1 - N Prestamo     (una copia se presta muchas veces a lo largo del tiempo)
#   * Estudiante 1 - N Prestamo   (un estudiante puede tener muchos préstamos)


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Autor(models.Model):
    nombre = models.CharField(max_length=150)

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    anio_publicacion = models.PositiveIntegerField()
    isbn = models.CharField(max_length=13, unique=True)
    # PROTECT: no se puede borrar una categoría que todavía tiene libros.
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    autores = models.ManyToManyField(Autor)
    # Agregado en la segunda migración; los libros ya existentes quedan en "Español".
    idioma = models.CharField(max_length=30, default="Español")

    def __str__(self):
        return f"{self.titulo} ({self.anio_publicacion})"


class Ejemplar(models.Model):
    CONDICIONES = [
        ("nuevo", "Nuevo"),
        ("usado", "Usado"),
        ("danado", "Dañado"),
    ]

    codigo_inventario = models.CharField(max_length=20, unique=True)
    condicion = models.CharField(max_length=10, choices=CONDICIONES, default="nuevo")
    # CASCADE: si se borra el libro, sus copias físicas dejan de tener sentido.
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.codigo_inventario} - {self.libro.titulo}"


class Estudiante(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Prestamo(models.Model):
    # PROTECT: no se puede borrar una copia ni un estudiante con historial de préstamos.
    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.PROTECT)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT)
    fecha_salida = models.DateField()
    fecha_limite = models.DateField()
    # Vacía mientras el libro no se ha devuelto (préstamo activo).
    fecha_devolucion = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            # Regla: una copia no puede estar prestada a dos personas al mismo tiempo.
            # Solo puede existir un préstamo sin fecha de devolución por ejemplar.
            models.UniqueConstraint(
                fields=["ejemplar"],
                condition=Q(fecha_devolucion__isnull=True),
                name="un_prestamo_activo_por_ejemplar",
            ),
        ]

    def __str__(self):
        return f"{self.ejemplar} -> {self.estudiante.nombre} ({self.fecha_salida})"
