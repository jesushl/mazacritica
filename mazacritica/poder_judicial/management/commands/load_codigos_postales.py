from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from poder_judicial.codigos_postales import load_codigos_postales


class Command(BaseCommand):
    help = 'Carga el catálogo SEPOMEX y lo empalma con municipios judiciales por clave y nombre.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default=str(Path(settings.BASE_DIR) / 'PoderJudicial_Data' / 'CPdescargatxt'),
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        if not data_dir.is_dir():
            raise CommandError(f'No existe el directorio de datos: {data_dir}')
        summary = load_codigos_postales(data_dir)
        self.stdout.write(
            'Códigos postales cargados: '
            f"{summary['codigos']} códigos, "
            f"{summary['municipios']} municipios, "
            f"{summary['asentamientos']} asentamientos."
        )
