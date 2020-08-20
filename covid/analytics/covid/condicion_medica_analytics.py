from django.db.models.query import QuerySet
from covid.models import MedicCondition, SiNo, Resultado, TipoPaciente
# dinamic filter
from covid.analytics.covid.dinamic_filtering import DinamicFilter

class MedicContionAnalitycs(DinamicFilter):
    def __init__(self):
      self.model = MedicCondition


  


  