import os

import openpyxl
import requests
from PIL import Image
from django.conf import settings
from django.http import HttpResponse, FileResponse, Http404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    FormView,
)
from urllib.parse import quote, unquote
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.urls import reverse

from six import BytesIO

from apps.product.filters import ProductFilter
from apps.product.models import Product, ProductImg, ProductCategory, PriceColumn
from apps.product.forms import (
    ProductForm,
    UploadExcelForm,
    ProductCategoryForm,
    PriceColumnForm,
)
from apps.provider.models import Category, Provider
from apps.user_cabinet.models import Contacts, OpenNumberCount


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    paginate_by = 10
    template_name = "products/product_list.html"
    filter_class = ProductFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        order = self.request.GET.get("order")
        if order:
            queryset = queryset.order_by(order)
        filter = self.filter_class(self.request.GET, queryset=queryset)
        return filter.qs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        contacts = Contacts.load()
        context["contacts"] = contacts
        return context


class ProductDetailView(DetailView):
    model = Product
    context_object_name = "product"
    template_name = "products/product_detail.html"

    def get_product_prices(self):
        product = self.get_object()
        prices = []
        formulas = PriceColumn.objects.filter(provider=self.object.provider)
        decimal = product.provider.decimal_places
        if formulas:
            for formula in formulas:
                prices.append(
                    {
                        "name": formula.name,
                        "price": formula.apply_formula(product.price),
                        "decimal": decimal,
                    }
                )
        else:
            prices.append({"name": "Цена", "price": product.price, "decimal": decimal})
        return prices

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context["categories"] = ProductCategory.objects.all()
        context["similar_products"] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:5]
        context["prices"] = self.get_product_prices()

        if self.request.GET.get("open"):
            if self.request.user.is_authenticated:
                print(self.get_object().provider.user)
                if self.get_object().provider.user.cabinet.user_status:
                    if (
                        self.get_object().user.cabinet.user_status.status.is_publish_phone
                    ):
                        OpenNumberCount.objects.create(
                            user=self.get_object().user.cabinet
                        )
                        context["open"] = "open"

        return context


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = "cabinet/products.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        provider, _ = Provider.objects.get_or_create(user=self.request.user)
        context['provider'] = provider
        return context

    def form_valid(self, form):
        provider = Provider.objects.get(user=self.request.user)
        form.instance.provider = provider
        response = super().form_valid(form)
        images = self.request.FILES.getlist("images")

        # Save the first image as the main image
        if images:
            main_image = images[0]
            product_img = ProductImg.objects.create(
                product=self.object, image=main_image
            )
            self.object.image = (
                main_image  # Assuming 'image' field exists in the Product model
            )
            self.object.save()

        # Save the rest of the images as additional images
        for image in images[1:]:
            ProductImg.objects.create(product=self.object, image=image)

        return response

    def form_invalid(self, form):
        print("Form invalid: %s", form.errors)
        return super().form_invalid(form)


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "cabinet/product_update.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ProductCategory.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images = self.request.FILES.getlist("images")
        if images:
            ProductImg.objects.filter(product=self.object).delete()
            main_image = images[0]
            self.object.image = main_image
            self.object.save()

        # Save the rest of the images as additional images
        for image in images[1:6]:  # Only process up to 5 additional images
            if image:
                ProductImg.objects.create(product=self.object, image=image)
        return response


class ProductDeleteView(DeleteView):
    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy("user_products")


class ExcelTemplateDownloadView(View):
    def get(self, request, *args, **kwargs):
        filepath = os.path.join(
            settings.BASE_DIR, "apps", "static", "excel", "template.xlsx"
        )
        filename = "Шаблон_добавления_продуктов.xlsx"
        with open(filepath, "rb") as excel_file:
            response = HttpResponse(
                excel_file.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f"attachment; filename*=UTF-8''{quote(filename)}"
            )
            return response



class DownloadPriceFileView(View):
    def get(self, request, *args, **kwargs):
        # Получение и декодирование относительного пути к файлу из параметров запроса
        relative_path = request.GET.get('filename')
        if not relative_path:
            print("Имя файла не указано")
            raise Http404("Имя файла не указано")

        # Декодирование пути
        safe_path = unquote(relative_path)

        # Построение полного пути к файлу
        filepath = os.path.join(settings.MEDIA_ROOT, safe_path)
        print(f"Attempting to access file at: {filepath}")

        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            raise Http404("Файл не найден")

        try:
            with open(filepath, "rb") as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(os.path.basename(filepath))}"
                return response
        except Exception as e:
            print(f"Error reading file: {e}")
            raise Http404("Ошибка при чтении файла")


class ExcelUploadView(FormView):
    template_name = "products/upload_file.html"
    form_class = UploadExcelForm
    success_url = reverse_lazy("user_products")

    def form_valid(self, form):
        form = self.form_class(self.request.POST, self.request.FILES)
        file = self.request.FILES.get("file")

        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        provider = Provider.objects.get(user=self.request.user)

        for row in sheet.iter_rows(min_row=3, values_only=True):
            try:
                category_instance, _ = ProductCategory.objects.get_or_create(
                    name=row[1], provider=provider
                )

                image_url = row[12]
                if image_url and isinstance(image_url, str):
                    print(image_url)
                    response = requests.get(image_url)
                    image = Image.open(BytesIO(response.content))
                    image_io = BytesIO()
                    image.save(image_io, format="WEBP")
                    image_content = ContentFile(image_io.getvalue(), name="image.webp")
                else:
                    image_content = None
                product = Product.objects.create(
                    provider=provider,
                    type=row[0],
                    category=category_instance,
                    title=row[2],
                    mini_desc=row[3],
                    description=row[4],
                    manufacturer=row[5],
                    price=row[6],
                    min_quantity=row[7],
                    terms_of_sale=row[8],
                    country_of_manufacture=row[9],
                    characterization=row[10],
                    phone=row[11],
                )
                if image_content:
                    product.image.save(image_content.name, image_content)
            except Exception as e:
                print(e)
                continue

        return super().form_valid(form)


class ProductCategoryCreateView(CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "cabinet/products.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ProductCategory.objects.filter(
            provider__user=self.request.user
        )
        return context

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        form.instance.provider = Provider.objects.get(user=self.request.user)

        return super().form_valid(form)


class ProductCategoryUpdateView(UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "cabinet/product_includes/edit_category.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ProductCategory.objects.filter(
            provider__user=self.request.user
        )
        return context

    def form_valid(self, form):
        form.instance.provider = self.request.user.provider
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)


class ProductCategoryDeleteView(DeleteView):
    model = ProductCategory
    template_name = "cabinet/product_includes/delete_category.html"
    success_url = reverse_lazy("user_products")


class PriceColumnCreateView(CreateView):
    model = PriceColumn
    form_class = PriceColumnForm
    template_name = "cabinet/products.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contacts = Contacts.load()
        context["contacts"] = contacts
        categories = ProductCategory.objects.filter(provider__user=self.request.user)
        context["categories"] = categories
        context["prices"] = PriceColumn.objects.filter(provider__user=self.request.user)
        context["decimal"] = self.request.user.provider.decimal_places
        if self.get_queryset().exists():
            context["has_products"] = True
        else:
            context["has_products"] = False

        return context

    def form_valid(self, form):
        form.instance.provider = self.request.user.provider

        # Получаем данные из формы
        post_data = self.request.POST
        names = post_data.getlist("name")
        formulas = post_data.getlist("formula")
        min_order_amounts = post_data.getlist("min_order_amount")
        decimal = post_data.get("decimal")
        form.instance.provider.decimal_places = decimal
        form.instance.provider.save()
        print(form.instance.provider.decimal_places)
        PriceColumn.objects.filter(provider__user=self.request.user).delete()
        # Обработка данных
        for index, (name, formula, min_order_amount) in enumerate(
            zip(names, formulas, min_order_amounts)
        ):
            # Если текущий индекс не равен последнему индексу в списке, создаем объект PriceColumn
            if index != len(names) - 1:
                PriceColumn.objects.create(
                    provider=form.instance.provider,
                    name=name,
                    formula=formula,
                    min_order_amount=min_order_amount,
                )

        return super().form_valid(form)

    def form_invalid(self, form):
        PriceColumn.objects.filter(provider__user=self.request.user).delete()
        return HttpResponseRedirect(reverse("user_products"))


class PriceColumnUpdateView(UpdateView):
    model = PriceColumn
    form_class = PriceColumnForm
    template_name = "cabinet/products.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contacts = Contacts.load()
        context["contacts"] = contacts
        categories = ProductCategory.objects.filter(provider__user=self.request.user)
        context["categories"] = categories
        context["prices"] = PriceColumn.objects.filter(provider__user=self.request.user)
        context["decimal"] = self.request.user.provider.decimal_places
        if self.get_queryset().exists():
            context["has_products"] = True
        else:
            context["has_products"] = False

        return context


class PriceColumnDeleteView(DeleteView):
    model = PriceColumn
    template_name = "cabinet/products.html"
    success_url = reverse_lazy("user_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contacts = Contacts.load()
        context["contacts"] = contacts
        categories = ProductCategory.objects.filter(provider__user=self.request.user)
        context["categories"] = categories
        context["prices"] = PriceColumn.objects.filter(provider__user=self.request.user)
        context["decimal"] = self.request.user.provider.decimal_places
        if self.get_queryset().exists():
            context["has_products"] = True
        else:
            context["has_products"] = False

        return context
