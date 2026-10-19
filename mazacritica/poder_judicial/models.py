from django.db import models


class Entidad(models.Model):
    clave = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=120, blank=True)
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['clave']
        verbose_name = 'entidad'

    def __str__(self):
        return self.nombre or str(self.clave)


class DistritoFederalElectoral(models.Model):
    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        related_name='distritos_federales',
    )
    numero = models.PositiveIntegerField()
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['entidad__clave', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['entidad', 'numero'],
                name='unique_distrito_federal_entidad_numero',
            ),
        ]
        verbose_name = 'distrito federal electoral'

    def __str__(self):
        return f'{self.entidad_id} distrito {self.numero}'


class CircuitoJudicial(models.Model):
    entidad = models.OneToOneField(
        Entidad,
        on_delete=models.PROTECT,
        related_name='circuito',
    )
    numero = models.PositiveIntegerField()
    romano = models.CharField(max_length=16)
    nombre = models.CharField(max_length=180)
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['numero']
        verbose_name = 'circuito judicial'

    def __str__(self):
        return self.nombre


class DistritoJudicialElectoral(models.Model):
    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        related_name='distritos_judiciales',
    )
    numero = models.PositiveIntegerField()
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['entidad__clave', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['entidad', 'numero'],
                name='unique_distrito_judicial_entidad_numero',
            ),
        ]
        verbose_name = 'distrito judicial electoral'

    def __str__(self):
        return f'{self.entidad_id} judicial {self.numero}'


class Municipio(models.Model):
    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        related_name='municipios',
    )
    clave = models.PositiveIntegerField()
    nombre = models.CharField(max_length=180, blank=True)
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['entidad__clave', 'clave']
        constraints = [
            models.UniqueConstraint(
                fields=['entidad', 'clave'],
                name='unique_municipio_entidad_clave',
            ),
        ]
        verbose_name = 'municipio'

    def __str__(self):
        return self.nombre or str(self.clave)


class SeccionElectoral(models.Model):
    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        related_name='secciones',
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.PROTECT,
        related_name='secciones',
    )
    numero = models.PositiveIntegerField()
    tipo = models.CharField(max_length=8, blank=True)
    tipo_nombre = models.CharField(max_length=40, blank=True)
    distrito_federal = models.ForeignKey(
        DistritoFederalElectoral,
        on_delete=models.PROTECT,
        related_name='secciones',
        null=True,
        blank=True,
    )
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['entidad__clave', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['entidad', 'numero'],
                name='unique_seccion_entidad_numero',
            ),
        ]
        verbose_name = 'sección electoral'

    def __str__(self):
        return f'{self.entidad_id} sección {self.numero}'


class AsignacionDistritoJudicial(models.Model):
    seccion = models.OneToOneField(
        SeccionElectoral,
        on_delete=models.CASCADE,
        related_name='asignacion_judicial',
    )
    distrito_judicial = models.ForeignKey(
        DistritoJudicialElectoral,
        on_delete=models.PROTECT,
        related_name='asignaciones',
    )
    circuito = models.ForeignKey(
        CircuitoJudicial,
        on_delete=models.PROTECT,
        related_name='asignaciones',
    )
    fuente = models.CharField(max_length=120)
    vigencia = models.DateField()

    class Meta:
        ordering = ['seccion_id']
        verbose_name = 'asignación de distrito judicial'

    def __str__(self):
        return f'{self.seccion_id} → {self.distrito_judicial_id}'


class Localidad(models.Model):
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.PROTECT,
        related_name='localidades',
    )
    clave = models.PositiveIntegerField()
    nombre = models.CharField(max_length=180, blank=True)
    tipo = models.CharField(max_length=8, blank=True)
    tipo_nombre = models.CharField(max_length=40, blank=True)
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['municipio_id', 'clave']
        constraints = [
            models.UniqueConstraint(
                fields=['municipio', 'clave'],
                name='unique_localidad_municipio_clave',
            ),
        ]
        verbose_name = 'localidad'

    def __str__(self):
        return self.nombre or str(self.clave)


class ManzanaGeoelectoral(models.Model):
    seccion = models.ForeignKey(
        SeccionElectoral,
        on_delete=models.CASCADE,
        related_name='manzanas',
    )
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.CASCADE,
        related_name='manzanas',
    )
    clave = models.CharField(max_length=16)
    status = models.CharField(max_length=8)
    fuente = models.CharField(max_length=120)

    class Meta:
        ordering = ['seccion_id', 'localidad_id', 'clave']
        constraints = [
            models.UniqueConstraint(
                fields=['seccion', 'localidad', 'clave'],
                name='unique_manzana_seccion_localidad_clave',
            ),
        ]
        verbose_name = 'manzana geoelectoral'

    def __str__(self):
        return self.clave


class SepomexMunicipio(models.Model):
    c_estado = models.PositiveIntegerField()
    c_mnpio = models.PositiveIntegerField()
    nombre = models.CharField(max_length=180)
    nombre_estado = models.CharField(max_length=120)
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sepomex',
    )

    class Meta:
        ordering = ['c_estado', 'c_mnpio']
        constraints = [
            models.UniqueConstraint(
                fields=['c_estado', 'c_mnpio'],
                name='unique_sepomex_estado_municipio',
            ),
        ]
        verbose_name = 'municipio SEPOMEX'

    def __str__(self):
        return f'{self.c_estado}/{self.c_mnpio} {self.nombre}'


class CodigoPostal(models.Model):
    codigo = models.CharField(max_length=5, unique=True)
    municipio = models.ForeignKey(
        SepomexMunicipio,
        on_delete=models.CASCADE,
        related_name='codigos',
    )

    class Meta:
        ordering = ['codigo']
        verbose_name = 'código postal SEPOMEX'

    def __str__(self):
        return self.codigo


class Asentamiento(models.Model):
    codigo = models.ForeignKey(
        CodigoPostal,
        on_delete=models.CASCADE,
        related_name='asentamientos',
    )
    clave = models.CharField(max_length=16)
    nombre = models.CharField(max_length=180)
    tipo = models.CharField(max_length=80)

    class Meta:
        ordering = ['codigo__codigo', 'clave']
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'clave'],
                name='unique_asentamiento_codigo_clave',
            ),
        ]
        verbose_name = 'asentamiento'

    def __str__(self):
        return self.nombre


class EmpalmePostalJudicial(models.Model):
    criterio = models.CharField(max_length=40, unique=True)
    vigencia = models.DateField()
    fuente_postal = models.CharField(max_length=120)
    fuente_judicial = models.CharField(max_length=180)

    class Meta:
        verbose_name = 'empalme postal judicial'

    def __str__(self):
        return self.criterio


class NoteMention(models.Model):
    candidate = models.ForeignKey(
        'api.Candidate',
        on_delete=models.CASCADE,
        related_name='note_mentions',
    )
    note = models.ForeignKey(
        'api.Note',
        on_delete=models.CASCADE,
        related_name='candidate_mentions',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'note'],
                name='unique_candidate_note_mention',
            ),
        ]
        ordering = ['candidate_id', 'note_id']

    def __str__(self):
        return f'{self.candidate_id} en {self.note_id}'
