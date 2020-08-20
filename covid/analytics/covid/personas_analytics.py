# dinamic filter
from covid.analytics.covid.dinamic_filtering import DinamicFilter
# models
from covid.models import Persona
# Filter
from covid.analytics.covid.dinamic_filtering import DinamicFilter

class PersonaAnalytics(DinamicFilter):
  def __init__(self):
    self.model = Persona