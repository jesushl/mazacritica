from django.db.models.query import QuerySet
from django.db import models

class DinamicFilter():
  
  def __init__(self):
    self.model = None

  def get_dinamic_filter(
      self,
      filter_dinamic:dict,
      medic_condition_query_set:QuerySet=None
    )->QuerySet:
      if not medic_condition_query_set:
        current_model_objects = self.model.objects
      return current_model_objects.filter(**filter_dinamic)

