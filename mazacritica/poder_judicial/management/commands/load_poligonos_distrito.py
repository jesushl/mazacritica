from pathlib import Path

from django.core.management.base import BaseCommand

from poder_judicial.poligonos import descargar_poligonos, ruta_poligonos


class Command(BaseCommand):
    help = 'Descarga los polígonos de distrito judicial electoral del SIGE del INE.'

    def add_arguments(self, parser):
        parser.add_argument('--destino', default=str(ruta_poligonos()))

    def handle(self, *args, **options):
        summary = descargar_poligonos(Path(options['destino']))
        self.stdout.write(
            'Polígonos judiciales descargados: '
            f"{summary['distritos']} distritos de {summary['circuitos']} circuitos."
        )
