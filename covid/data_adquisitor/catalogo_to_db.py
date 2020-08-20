# PANDAS
import pandas as pd
from pandas import DataFrame 
# Models
from django.db.models import Model
from covid.models import Origen, Sector,Sexo
from covid.models import TipoPaciente, SiNo, Nacionalidad
from covid.models import Resultado, Entidad, Municipio


class CatalogoFillter():
  def __init__(
    self,
    catalogo_file:str
  )->None:
    self.catalogo_file=catalogo_file
    self.sheet_catalog={
      'origen': 0,
      'sector': 1,
      'sexo': 2,
      'tipo_paciente': 3,
      'si_no': 4,
      'nacionalidad': 5,
      'resultado': 6,
      'entidades': 7,
      'municipios': 8
    }
  
  def fill_catalogo_entities(
    self
    ):
      self.fill_origen(self.catalogo_file)
      self.fill_sector(self.catalogo_file)
      self.fill_sexo(self.catalogo_file)
      self.fill_tipo_paciente(self.catalogo_file)
      self.fill_si_no(self.catalogo_file)
      self.fill_nacionalidad(self.catalogo_file)
      self.fill_resultado(self.catalogo_file)
      self.fill_entidades(self.catalogo_file)
      self.fill_municipios(self.catalogo_file)

  def fill_municipios(
    self,
    catalogo_file
  ):
    sheed_index = self.sheet_catalog.get('municipios')
    sheed_records = self.open_sheet(
      catalogo_file=catalogo_file,
      sheed_index=sheed_index
    ).to_records(index=False)
    Municipio.objects.all().delete()
    print('filling Municipios')
    municipios = len(sheed_records)
    salvados = 0
    for record in sheed_records:
      clave_entidad = int(record[2])
      entidad = Entidad.objects.get(clave=clave_entidad)
      Municipio(
        clave=int(record[0]),
        municipio=record[1],
        entidad=entidad
      ).save()
      salvados = salvados +1
      print(' ' * 50, end="\r")
      print('{salvados} / {por_salvar} {municipio}'.format(
        salvados=salvados, 
        por_salvar=municipios,  
        municipio=record[1]), end='\r'
      )
    print('Municipios filled')

  def fill_entidades(
    self,
    catalogo_file
  ):
    sheed_index = self.sheet_catalog.get('entidades')
    sheed_records = self.open_sheet(
      catalogo_file=catalogo_file,
      sheed_index=sheed_index
    ).to_records(index=False)
    Entidad.objects.all().delete()
    print('Filling entiaddes')
    for record in sheed_records:
      Entidad(
        clave=int(record[0]),
        entidad_federativa=record[1],
        abreviatura=record[2]
      ).save()


  def fill_resultado(
    self,
    catalogo_file:str
  ):
    self.fill_model(
      catalogo_file,
      'resultado',
      Resultado
    )

  def fill_nacionalidad(
    self,
    catalogo_file:str
  ):
    self.fill_model(
      catalogo_file,
      'nacionalidad',
      Nacionalidad
    )

  def fill_si_no(
    self,
    catalogo_file
    ):
      self.fill_model(
        catalogo_file,
        'si_no',
        SiNo
      )
  
  def fill_tipo_paciente(
    self,
    catalogo_file:str
  ):
    self.fill_model(
      catalogo_file,
      'tipo_paciente',
      TipoPaciente
    )

  def fill_sexo(
    self,
    catalogo_file:str
  ):
    self.fill_model(
      catalogo_file,
      'sexo',
      Sexo
    )

  def fill_sector(
    self,
    catalogo_file:str
  ):
    self.fill_model(
      catalogo_file,
      'sector',
      Sector
    )


  def fill_origen(
    self,
    catalogo_file:str
  ):
    self.fill_model(
      catalogo_file,
      'origen',
      Origen
    )


  def fill_model(
    self,
    catalogo_file:str,
    sheed_name_index:str,
    model:Model
    ):
      sheed_index = self.sheet_catalog.get(sheed_name_index)
      sheed_df = self.open_sheet(
        catalogo_file=catalogo_file,
        sheed_index=sheed_index
      )
      self.fill_entity_clave_descripcion(
        model=model,
        data_frame=sheed_df
      )

  def fill_entity_clave_descripcion(
    self,
    model:Model,
    data_frame:DataFrame
  )->None:
    records = data_frame.to_records(index=False)
    model.objects.all().delete()
    print('Filling : {}'.format(model))
    for record in records:
      try:
        clave = int(record[0])
        model(
          clave=clave,
          descripcion=record[1]
        ).save()
      except ValueError as ve:
        pass

  def open_sheet(
    self,
    catalogo_file:str,
    sheed_index:int
  )->DataFrame:
    return pd.read_excel(catalogo_file, sheet_name=sheed_index)


if __name__ == '__main__':
  cf = CatalogoFillter(catalogo_file=catalogo_file)
  catalogo_file = "/home/jesus/Proyectos/mazacritica/static/diccionario_datos_covid19/Catalogos_0412.xlsx"
  cf.fill_catalogo_entities()