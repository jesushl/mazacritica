from datetime import datetime
import re
import pickle
# therading
import threading
# external
import pandas as pd 
from pandas import DataFrame
# models
from covid.models import Persona, Entidad 
from covid.models import Municipio, Origen, Sector
from covid.models import Sexo, TipoPaciente, SiNo
from covid.models import  Nacionalidad, Resultado
from covid.models import MedicCondition
from covid.models import SiNo, Usmer
# models tools
from django.forms.models import model_to_dict
# Error
from django.db import DataError

class ContagiosCSVToDataBase():
  
  def __init__(
    self,
    csv_file:str
  ):
    self.csv_file = csv_file
    self.date_format= '%Y-%m-%d'
    self.default_date = re.compile('9999-99-99')
    """
    si_no_1 = SiNo.objects.get(clave=1)
    si_no_2 = SiNo.objects.get(clave=2)
    si_no_97 = SiNo.objects.get(clave=97)
    si_no_98 = SiNo.objects.get(clave=98)
    si_no_99 = SiNo.objects.get(clave=99)
    """
    self.si_no_dict = {
      1: SiNo.objects.get(clave=1),
      2: SiNo.objects.get(clave=2),
      97: SiNo.objects.get(clave=97),
      98: SiNo.objects.get(clave=98),
      99: SiNo.objects.get(clave=99)
    }
    """
    resultado_1 = Resultado.objects.get(clave=1)
    resultado_2 = Resultado.objects.get(clave=2)
    resultado_3 = Resultado.objects.get(clave=3)
    """
    self.resultado_dict = {
      1: Resultado.objects.get(clave=1),
      2: Resultado.objects.get(clave=2),
      3: Resultado.objects.get(clave=3),
    }
    """
    origen_1 = Origen.objects.get(clave=1)
    origen_2 = Origen.objects.get(clave=2)
    origen_99 = Origen.objects.get(clave=99)
    """
    self.origen_dict = {
      1: Origen.objects.get(clave=1),
      2: Origen.objects.get(clave=2),
      99: Origen.objects.get(clave=99)
    }
    self.sector_dict = {}
    self.sexo_dict = {}
    self.tipo_paciente_dict = {}
    self.nacionaliodad_dict = {}
    self.entidades_dict = {}
    self.municipio_dict = {}
    self.origen_dict = {}
    self.sector_dict = {}
    self.entidad_um_dict = {}
    # Column definitions
    self.fecha_actualizacion = 'FECHA_ACTUALIZACION'
    self.id_registro =  'ID_REGISTRO'
    self.origen = 'ORIGEN'
    self.sector = 'SECTOR'
    self.entidad_um =  'ENTIDAD_UM'
    self.sexo = 'SEXO' 
    self.entidad_nac = 'ENTIDAD_NAC'
    self.entidad_res =  'ENTIDAD_RES'
    self.municipio_res =   'MUNICIPIO_RES' 
    self.tipo_paciente =  'TIPO_PACIENTE'
    self.fecha_ingreso = 'FECHA_INGRESO'
    self.fecha_sintomas = 'FECHA_SINTOMAS'
    self.fecha_def =  'FECHA_DEF'
    self.intubado =  'INTUBADO'
    self.neumonia = 'NEUMONIA'
    self.edad =  'EDAD'
    self.nacionalidad = 'NACIONALIDAD'
    self.embarazo = 'EMBARAZO'
    self.habla_lengua_idigena =  'HABLA_LENGUA_INDIG'
    self.diabetes = 'DIABETES'
    self.epoc = 'EPOC'
    self.asma = 'ASMA'
    self.imnuno_suprimido = 'INMUSUPR'
    self.hipertencion = 'HIPERTENSION'
    self.otra_complicacion =  'OTRA_COM'
    self.cardiovacular =  'CARDIOVASCULAR'
    self.obesidad =  'OBESIDAD'
    self.renal_cronica =  'RENAL_CRONICA'
    self.tabaquismo =  'TABAQUISMO'
    self.otro_caso =  'OTRO_CASO'
    self.resultado_covid= 'RESULTADO'
    self.migrante =  'MIGRANTE'
    self.pais_de_nacionalidad = 'PAIS_NACIONALIDAD'
    self.pais_de_origen ='PAIS_ORIGEN'
    self.respirador_uci ='UCI'
    self.clave_descriptor = 'clave'

  def fill_model(self):
    records  = pd.read_csv(
      self.csv_file, sep=',', encoding="ISO-8859-1"
    )
    # Use datetime insted strings
    records[self.fecha_actualizacion]=pd.to_datetime(records[self.fecha_actualizacion])
    records[self.fecha_ingreso]=pd.to_datetime(records[self.fecha_ingreso])
    records[self.fecha_sintomas] =pd.to_datetime(records[self.fecha_sintomas])
    # Moving into every record
    total_people = len(records[self.id_registro])
    num_personas = Persona.objects.all().count()
    missed_people = total_people - num_personas
    print('People on database : {num_personas}   Missing people: {missed_people}'.format(
        num_personas=num_personas,
        missed_people=missed_people
      )
    )
    level_1 = int(total_people / 4)
    range_thread_1 = range(0,level_1)
    level_2 = level_1 + level_1
    range_thread_2 = range(level_1, level_2)
    level_3 = level_2 + level_1
    range_thread_3 = range(level_2, level_3)
    range_thread_4 = range(level_3, total_people)
    set_person = self.set_person
    t_1 = threading.Thread(target=set_person, args=(range_thread_1, records,))
    t_2 = threading.Thread(target=set_person, args=(range_thread_2, records,))
    t_3 = threading.Thread(target=set_person, args=(range_thread_3, records,))
    t_4 = threading.Thread(target=set_person, args=(range_thread_4, records,))
    threads = list()
    threads.append(t_1)
    threads.append(t_2)
    threads.append(t_3)
    threads.append(t_4)
    t_1.start()
    t_2.start()
    t_3.start()
    t_4.start()
    print("Threads finished")

  def string_to_datetime(
    self,
    date:str
  ):
    return datetime.strptime(date, self.date_format)
  

  def set_person(
    self,
    range:range,
    records:DataFrame
  )->None:
    processed=0
    
    for index in range:
      _id_registro = records[self.id_registro][index]
      processed = processed + 1
      try:
        persona = Persona.objects.get(id_registro=_id_registro)
        print(' ' * 50, end='\r')
        print("{processed} ".format(
          processed=processed
        ), end='\r')

      except Persona.DoesNotExist:
        # Get Residencia
        entidad_rec = self.get_cool_entity(
          entities_dict = self.entidades_dict,
          model=Entidad,
          clave = self.clave_descriptor, 
          value = records[self.entidad_res][index] 
        )
        municipio_rec = Municipio.objects.get_or_create(
          clave = records[self.municipio_res][index],
          entidad=entidad_rec,
          municipio=records[self.municipio_res][index]
        )[0]
        _sexo = self.get_cool_entity(
          entities_dict = self.sexo_dict,
          model=Sexo,
          clave = self.clave_descriptor, 
          value = records[self.sexo][index] 
        )
        _entidad_nac = self.get_cool_entity(
          entities_dict = self.entidades_dict,
          model=Entidad,
          clave = self.clave_descriptor, 
          value = records[self.entidad_nac][index] 
        )
        _edad = records[self.edad][index]
        _nacionalidad = self.get_cool_entity(
          entities_dict = self.nacionaliodad_dict,
          model=Nacionalidad,
          clave = self.clave_descriptor, 
          value = records[self.nacionalidad][index] 
        )
        _habla_lengua_indigena = self.si_no_dict[
          records[self.habla_lengua_idigena][index]
        ]
        _migrante = self.si_no_dict[
          records[self.migrante][index]
        ]
        _pais_nacionalidad = records[self.pais_de_nacionalidad][index]
        _pais_origen = records[self.pais_de_origen][index]
        
        # Create a Person to update or create
        persona = Persona(
          residencia=municipio_rec,
          id_registro=_id_registro,
          sexo=_sexo,
          entidad_nac=_entidad_nac,
          edad=_edad,
          nacionalidad=_nacionalidad,
          habla_lengua_indigena=_habla_lengua_indigena,
          migrante=_migrante,
          pais_nacionalidad=_pais_nacionalidad,
          pais_origen=_pais_origen
        )
        persona.save()
      # USMER
      _origen = self.get_cool_entity(
        entities_dict = self.origen_dict,
        model=Origen,
        clave = self.clave_descriptor, 
        value = records[self.origen][index] 
      )
      _sector = self.get_cool_entity(
        entities_dict = self.sector_dict,
        model=Sector,
        clave = self.clave_descriptor, 
        value = records[self.sector][index] 
      )
      _entidad_um = self.get_cool_entity(
        entities_dict = self.entidades_dict,
        model=Entidad,
        clave = self.clave_descriptor, 
        value = records[self.entidad_um][index] 
      )
      self.add_medic_condition(
        persona=persona,
        records=records,
        index=index
      )
      usmer = Usmer.objects.get_or_create(
        persona=persona,
        origen =_origen,
        sector=_sector,
        entidad_um=_entidad_um
      )
      print(' ' * 50, end='\r')
      print("{processed} ".format(
        processed=processed
      ), end='\r')
    # Set users


  def add_medic_condition(
    self, 
    persona,
    records,
    index
  ):
    try:
      last_estado_clinico = MedicCondition.objects.filter(persona=persona).order_by('created_at')
      last_estado_clinico=last_estado_clinico[0]
    except MedicCondition.DoesNotExist:
      last_estado_clinico = None
    except IndexError:
      last_estado_clinico = None

    _fecha_actualizacion = records[self.fecha_actualizacion][index]
    _tipo_paciente = self.get_cool_entity(
      entities_dict = self.tipo_paciente_dict,
      model=TipoPaciente,
      clave = self.clave_descriptor, 
      value = records[self.tipo_paciente][index] 
    )
    _fecha_ingreso=records[self.fecha_ingreso][index]
    _fecha_sintomas=records[self.fecha_sintomas][index]
    _fecha_defuncion = self.get_defuncion_date(
      records[self.fecha_def][index]
    )
    _intubado =  self.si_no_dict[records[self.intubado][index]]
    _neumonia = self.si_no_dict[records[self.neumonia][index]]
    _embarazo = self.si_no_dict[records[self.embarazo][index]]
    _diabetes = self.si_no_dict[records[self.diabetes][index]]
    _epoc = self.si_no_dict[records[self.epoc][index]]
    _asma = self.si_no_dict[records[self.asma][index]]
    _inmuno_supresion = self.si_no_dict[records[self.imnuno_suprimido][index]]
    _hipertencion = self.si_no_dict[records[self.hipertencion][index]]
    _otras_complicaciones = self.si_no_dict[records[self.otro_caso][index]]
    _cardiovascular = self.si_no_dict[records[self.cardiovacular][index]]
    _obesidad = self.si_no_dict[records[self.obesidad][index]]
    _renal_cronica = self.si_no_dict[records[self.renal_cronica][index]]
    _tabaquismo = self.si_no_dict[records[self.tabaquismo][index]]
    _otro_caso = self.si_no_dict[records[self.otro_caso][index]]
    _resultado = self.get_cool_entity(
      entities_dict = self.resultado_dict,
      model=Resultado,
      clave = self.clave_descriptor, 
      value = records[self.resultado_covid][index] 
    )
    _uci = self.si_no_dict[records[self.respirador_uci][index]]
    medic_condition = MedicCondition(
      persona = persona,
      tipo_paciente=_tipo_paciente,
      fecha_ingreso=_fecha_ingreso,
      fecha_sintomas=_fecha_sintomas,
      fecha_defuncion=_fecha_defuncion,
      intubado=_intubado,
      neumonia=_neumonia, 
      embarazo=_embarazo,
      diabetes=_diabetes,
      epoc=_epoc,
      asma=_asma,
      inmuno_supresion=_inmuno_supresion,
      hipertencion=_hipertencion,
      otras_complicaciones=_otras_complicaciones,
      cardiovascular=_cardiovascular,
      obesidad=_obesidad,
      renal_cronica=_renal_cronica, 
      tabaquismo=_tabaquismo,
      otro_caso=_otro_caso,
      resultado=_resultado,
      uci=_uci,
    )
    if self.is_new_condition(
      new_condition=medic_condition,
      old_medic_condition=last_estado_clinico
    ):
      medic_condition.save()
    
  def is_new_condition(
    self,
    old_medic_condition,
    new_condition
  )->bool:
    same = False 
    if not old_medic_condition:
      return same 
    else:
      return   not (
        (old_medic_condition.intubado==new_condition.intubado) or
        (old_medic_condition.neumonia==new_condition.neumonia) or
        (old_medic_condition.embarazo==new_condition.embarazo) or
        (old_medic_condition.diabetes==new_condition.diabetes) or
        (old_medic_condition.epoc==new_condition.epoc) or 
        (old_medic_condition.asma==new_condition.asma) or 
        (old_medic_condition.inmuno_supresion==new_condition.inmuno_supresion) or 
        (old_medic_condition.hipertencion==new_condition.hipertencion) or
        (old_medic_condition.otras_complicaciones==new_condition.otras_complicaciones) or 
        (old_medic_condition.cardiovascular==new_condition.cardiovascular) or
        (old_medic_condition.obesidad==new_condition.obesidad) or
        (old_medic_condition.renal_cronica==new_condition.renal_cronica) or
        (old_medic_condition.tabaquismo==new_condition.tabaquismo) or 
        (old_medic_condition.otro_caso==new_condition.otro_caso) or 
        (old_medic_condition.resultado==new_condition.resultado) or 
        (old_medic_condition.uci==new_condition.uci)
      )



  def get_defuncion_date(self, def_date):
    if self.is_default_date(def_date):
      return None 
    else:
      return self.string_to_datetime(def_date)

  def is_default_date(self, def_date):
    is_default = False
    if self.default_date.search(def_date):
      is_default=True
    return is_default

  def get_cool_entity(self, entities_dict, model, clave , value):
    if clave in entities_dict:
      return model(entities_dict[value])
    else:
      try:
        _entity_object = model.objects.get(**{clave: value})
        entities_dict.update(
          {
            value: model_to_dict(_entity_object)
          }
        )
      except model.DoesNotExist:
        pass
      except model.MultipleObjectsReturned:
        pass
      return _entity_object


