# Generated manually to add server_category field to MonitoringServerInformation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kylinApp', '0002_databaseinformationmanagement_remarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoringserverinformation',
            name='server_category',
            field=models.CharField(blank=True, default='', max_length=32, verbose_name='服务类型'),
        ),
    ]
