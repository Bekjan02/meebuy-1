# Generated by Django 4.2.11 on 2024-06-13 10:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0001_initial'),
        ('provider', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product_categories', to='provider.provider'),
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='product.productcategory', verbose_name='Категория'),
        ),
        migrations.AddField(
            model_name='product',
            name='provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='provider.provider'),
        ),
        migrations.AddField(
            model_name='pricecolumn',
            name='provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prices', to='provider.provider'),
        ),
    ]
