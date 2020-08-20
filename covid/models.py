from django.db import models



"""
Catalogo models 0412
"""
class Origen(models.Model):
  descripcion= models.CharField(max_length=25)
  clave = models.IntegerField()
  
class Sector(models.Model):
  clave=models.IntegerField()
  descripcion=models.CharField(max_length=40)

class Sexo(models.Model):
  descripcion=models.CharField(max_length=30)
  clave=models.IntegerField()

class TipoPaciente(models.Model):
  descripcion=models.CharField(max_length=30)
  clave=models.IntegerField()

class SiNo(models.Model):
  descripcion=models.CharField(max_length=30)
  clave=models.IntegerField()

class Nacionalidad(models.Model):
  descripcion=models.CharField(max_length=30)
  clave=models.IntegerField()

class Resultado(models.Model):
  descripcion=models.CharField(max_length=30)
  clave=models.IntegerField()

class Entidad(models.Model):
  clave=models.IntegerField()
  entidad_federativa=models.CharField(max_length=100)
  abreviatura=models.CharField(max_length=4)

class Municipio(models.Model):
  clave=models.IntegerField()
  municipio=models.CharField(max_length=100)
  entidad=models.ForeignKey(Entidad, on_delete=models.CASCADE)
  
  """
  datos abiertos
  https://www.gob.mx/salud/documentos/datos-abiertos-152127
  http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/datos_abiertos_covid19.zip
  """

# unidades monitoras de enfermedad respiratoria viral (USMER)
# El sistema no cuenta a la gente que se recupera... la unica manera de saber si alguien recallo es ver si el ingreso cambia

class Persona(models.Model):
  residencia = models.ForeignKey(Municipio, on_delete=models.CASCADE,null=False, blank=False)
  id_registro=models.CharField(max_length=7, primary_key=True)
  sexo=models.ForeignKey(Sexo, on_delete=models.CASCADE)
  entidad_nac=models.ForeignKey(Entidad,on_delete=models.CASCADE, related_name='entidad_nacimiento')
  edad=models.IntegerField() # Inferir fecha de nacimiento
  nacionalidad=models.ForeignKey(Nacionalidad, on_delete=models.CASCADE)
  habla_lengua_indigena=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='habla_lengua_indigena_si_no')
  migrante=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='migrante_si_no')
  pais_nacionalidad=models.CharField(max_length=100)
  pais_origen=models.CharField(max_length=100)
  # Create and update automated
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def is_changed(self, other_persona):
    excluded_keys=['id_registro', 'id', 'created_at', 'updated_at' ]
    return self._is_changed(self, other_persona, excluded_keys)
  
  def _is_changed(self, obj1, obj2, excluded_keys=[]):
    changed = False
    d1, d2 = obj1.__dict__, obj2.__dict__ 
    for k, v in d1.items():
      if k in excluded_keys:
        continue 
      try:
        if v != d2[k]:
          changed=True
      except KeyError :
        raise ValueError
    return changed

class MedicCondition(models.Model):
  persona=models.ForeignKey(Persona, on_delete=models.CASCADE)
  tipo_paciente=models.ForeignKey(TipoPaciente,on_delete=models.CASCADE)
  fecha_ingreso=models.DateField()
  fecha_sintomas=models.DateField()
  fecha_defuncion=models.DateField(null=True, blank=True)
  intubado=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='entubado_si_no')
  neumonia=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='neumonia_si_no')
  embarazo=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='embarazo_si_no')
  diabetes=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='diabetes_si_no')
  epoc=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='epoc_si_no')
  asma=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='asma_si_no')
  inmuno_supresion=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='inmuno_si_no')
  hipertencion=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='hipertencion_si_no')
  otras_complicaciones=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='otras_complicaciones_si_no')
  cardiovascular=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='cardio_vascular_si_no')
  obesidad=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='obesidad_si_no')
  renal_cronica=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='renal_cronica_si_no')
  tabaquismo=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='tabaquismo_si_no')
  otro_caso=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='otro_caso_si_no')
  resultado=models.ForeignKey(Resultado, on_delete=models.CASCADE) # Tiene o no covid
  uci=models.ForeignKey(SiNo, on_delete=models.CASCADE, related_name='uci_si_no')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  
  
class Usmer(models.Model):
  persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
  origen=models.ForeignKey(Origen, on_delete=models.CASCADE)
  sector=models.ForeignKey(Sector, on_delete=models.CASCADE)
  entidad_um=models.ForeignKey(Entidad, on_delete=models.CASCADE)
