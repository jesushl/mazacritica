from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from poder_judicial.geoelectoral import load_geoelectoral


class Command(BaseCommand):
    help = 'Carga el catálogo geoelectoral y el corte de distritos judiciales.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default=str(Path(settings.BASE_DIR) / 'PoderJudicial_Data'),
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        if not data_dir.is_dir():
            raise CommandError(f'No existe el directorio de datos: {data_dir}')
        summary = load_geoelectoral(data_dir)
        self.stdout.write(
            'Catálogo geoelectoral cargado: '
            f"{summary['secciones']} secciones, "
            f"{summary['asignaciones']} asignaciones judiciales, "
            f"{summary['manzanas']} manzanas."
        )
