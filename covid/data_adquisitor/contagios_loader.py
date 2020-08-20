# python
import os 
import pathlib
import zipfile
from datetime import datetime
# covid
from covid.data_adquisitor.contagios_to_db import ContagiosCSVToDataBase
class ContagiosActualizer():

  def __init__(
    self
  ):
    # http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/datos_abiertos_covid19.zip
    pass 
  
  def load_zip_ccv_file(
    self,
    destiny:str=None,
    file_to_load:str= "http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/datos_abiertos_covid19.zip"
  )->None:
    command = "wget -P {destiny} {file_to_load}".format(destiny=destiny,file_to_load=file_to_load)
    os.system(command)
  
  def unzip_file(
    self,
    file_to_unzip:str,
    destination_file:str
  )->None:
    with zipfile.ZipFile(file_to_unzip,'r') as zip_ref:
      zip_ref.extractall(destination_file)
  
  def actualize_database(
    self,
    csv_file:str
  ):
    contagios_from_csv_to_db = ContagiosCSVToDataBase(csv_file=csv_file)
    contagios_from_csv_to_db.fill_model()

  def actualize(
    self
  ):
    now = datetime.now()
    now = now.strftime("%d%m%Y")
    dir_path = pathlib.Path().absolute()
    general_destiny_file = '{dir_path}/openData/{now}'.format(
      dir_path=dir_path,
      now=now
    )
    zip_destiny = "{general_destiny_file}".format(general_destiny_file=general_destiny_file)
    csv_destiny = "{general_destiny_file}".format(
      general_destiny_file=general_destiny_file,
      now=now
      )
    zip_file = "{csv_destiny}/datos_abiertos_covid19.zip".format(csv_destiny=csv_destiny)
    # Load
    self.load_zip_ccv_file(destiny=zip_destiny) # Good
    # Unzip
   
    self.unzip_file(
      file_to_unzip=zip_file,
      destination_file=csv_destiny
    )
    unziped_files = os.listdir(csv_destiny)
    csv_file = None 
    for files in unziped_files:
      if 'csv' in files:
        csv_file = files
        break
    # Actualize
    self.actualize_database(
      csv_file="{csv_destiny}/{csv_file}".format(
        csv_destiny=csv_destiny, 
        csv_file=csv_file
      )
    )

