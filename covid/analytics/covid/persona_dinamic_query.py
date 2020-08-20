# Models
from django.db.models.query import QuerySet
from covid.models import Persona, SiNo, Residencia, Entidad, Nacionalidad
# Filter
from covid.analytics.covid.dinamic_filtering import DinamicFilter

class PersonaDinamicQuery():
  
  def __init__(
    self
  ):
    self.objects_definitions = {
      'persona': Persona
    }

  def make_dinamic_query(
    self,
    request
  )->QuerySet:
    pass
  

  
