from django.contrib import admin
from django.utils import timezone

from .models import Autor, Categoria, Ejemplar, Estudiante, Libro, Prestamo


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


# Inline: las copias físicas se ven y se editan DENTRO de la página del libro.
class EjemplarInline(admin.TabularInline):
    model = Ejemplar
    extra = 1  # deja una fila vacía lista para agregar otra copia


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "anio_publicacion", "isbn", "categoria", "idioma")
    search_fields = ("titulo", "isbn")
    list_filter = ("categoria", "idioma")
    inlines = [EjemplarInline]
    readonly_fields = ("total_ejemplares",)  # se muestra pero no se edita

    @admin.display(description="Total de copias")
    def total_ejemplares(self, obj):
        if not obj.pk:  # libro nuevo, todavía sin guardar: no tiene copias
            return 0
        return obj.ejemplar_set.count()


@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display = ("codigo_inventario", "libro", "condicion")
    search_fields = ("codigo_inventario", "libro__titulo")
    list_filter = ("condicion",)
    ordering = ("codigo_inventario",)
    list_select_related = ("libro",)  # evita una consulta extra por fila (N+1)


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "correo")
    search_fields = ("codigo", "nombre")  # busca por código O por nombre


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "ejemplar",
        "estudiante",
        "fecha_salida",
        "fecha_limite",
        "fecha_devolucion",
        "devuelto",
    )
    # "Vacío" en fecha_devolucion = préstamos que siguen sin devolverse
    list_filter = (("fecha_devolucion", admin.EmptyFieldListFilter), "fecha_limite")
    search_fields = (
        "estudiante__nombre",
        "estudiante__codigo",
        "ejemplar__codigo_inventario",
        "ejemplar__libro__titulo",
    )
    # Buscador en vez de una lista gigante de copias/estudiantes
    autocomplete_fields = ("ejemplar", "estudiante")
    list_select_related = ("ejemplar__libro", "estudiante")
    actions = ["marcar_como_devueltos"]

    @admin.display(boolean=True, description="¿Devuelto?")
    def devuelto(self, obj):
        return obj.fecha_devolucion is not None

    @admin.action(description="Marcar préstamos seleccionados como devueltos")
    def marcar_como_devueltos(self, request, queryset):
        actualizados = queryset.filter(fecha_devolucion__isnull=True).update(
            fecha_devolucion=timezone.localdate()
        )
        self.message_user(request, f"{actualizados} préstamo(s) marcado(s) como devueltos.")