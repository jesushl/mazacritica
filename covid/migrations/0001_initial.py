# Generated by Django 3.0.7 on 2020-08-15 06:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Entidad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.IntegerField()),
                ('entidad_federativa', models.CharField(max_length=100)),
                ('abreviatura', models.CharField(max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.IntegerField()),
                ('municipio', models.CharField(max_length=100)),
                ('entidad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Entidad')),
            ],
        ),
        migrations.CreateModel(
            name='Nacionalidad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=30)),
                ('clave', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Origen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=25)),
                ('clave', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Persona',
            fields=[
                ('id_registro', models.CharField(max_length=7, primary_key=True, serialize=False)),
                ('edad', models.IntegerField()),
                ('pais_nacionalidad', models.CharField(max_length=100)),
                ('pais_origen', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('entidad_nac', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entidad_nacimiento', to='covid.Entidad')),
            ],
        ),
        migrations.CreateModel(
            name='Resultado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=30)),
                ('clave', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.IntegerField()),
                ('descripcion', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Sexo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=30)),
                ('clave', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='SiNo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=30)),
                ('clave', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TipoPaciente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=30)),
                ('clave', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Usmer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entidad_um', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Entidad')),
                ('origen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Origen')),
                ('persona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Persona')),
                ('sector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Sector')),
            ],
        ),
        migrations.CreateModel(
            name='Residencia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entidad_res', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entidad_recidencia', to='covid.Entidad')),
                ('municipio_res', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='municipio_recidencia', to='covid.Municipio')),
            ],
        ),
        migrations.AddField(
            model_name='persona',
            name='habla_lengua_indigena',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='habla_lengua_indigena_si_no', to='covid.SiNo'),
        ),
        migrations.AddField(
            model_name='persona',
            name='migrante',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='migrante_si_no', to='covid.SiNo'),
        ),
        migrations.AddField(
            model_name='persona',
            name='nacionalidad',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Nacionalidad'),
        ),
        migrations.AddField(
            model_name='persona',
            name='residencia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Residencia'),
        ),
        migrations.AddField(
            model_name='persona',
            name='sexo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Sexo'),
        ),
        migrations.CreateModel(
            name='MedicCondition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_ingreso', models.DateField()),
                ('fecha_sintomas', models.DateField()),
                ('fecha_defuncion', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asma_si_no', to='covid.SiNo')),
                ('cardiovascular', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cardio_vascular_si_no', to='covid.SiNo')),
                ('diabetes', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diabetes_si_no', to='covid.SiNo')),
                ('embarazo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='embarazo_si_no', to='covid.SiNo')),
                ('epoc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='epoc_si_no', to='covid.SiNo')),
                ('hipertencion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hipertencion_si_no', to='covid.SiNo')),
                ('inmuno_supresion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inmuno_si_no', to='covid.SiNo')),
                ('intubado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entubado_si_no', to='covid.SiNo')),
                ('neumonia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='neumonia_si_no', to='covid.SiNo')),
                ('obesidad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obesidad_si_no', to='covid.SiNo')),
                ('otras_complicaciones', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otras_complicaciones_si_no', to='covid.SiNo')),
                ('otro_caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otro_caso_si_no', to='covid.SiNo')),
                ('persona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Persona')),
                ('renal_cronica', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='renal_cronica_si_no', to='covid.SiNo')),
                ('resultado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.Resultado')),
                ('tabaquismo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tabaquismo_si_no', to='covid.SiNo')),
                ('tipo_paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='covid.TipoPaciente')),
                ('uci', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uci_si_no', to='covid.SiNo')),
            ],
        ),
    ]