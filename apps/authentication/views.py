from django.views.generic import TemplateView, FormView, UpdateView, RedirectView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist


from apps.authentication.forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserTypeSelectionForm
from apps.buyer.models import Buyer
from apps.product.models import Product
from apps.tender.models import Tender
from apps.provider.models import Provider, Category
from apps.user_cabinet.models import Cabinet, Contacts

class HomeView(TemplateView):
    template_name = 'auth/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rec_products'] = Product.objects.all()[:6]
        context['new_products'] = Product.objects.all()[:6]
        context['new_providers'] = Provider.objects.filter(is_modered=True, is_provider=True)[:4]
        context['categories'] = Category.objects.filter(category=None)
        context['tenders'] = Tender.objects.all()[:8]
        contacts = Contacts.load()
        context['contacts'] = contacts
        return context


class LoginView(FormView):
    form_class = UserLoginForm
    template_name = 'auth/auth.html'
    success_url = reverse_lazy('view_profile')

    def post(self, request, *args, **kwargs):
        if request.POST.get('password1'):
            register_form = UserRegistrationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save(commit=False)
                user.auth_provider = False
                user.save()
                Cabinet.objects.get_or_create(user=user)
                authenticated_user = authenticate(email=user.email, password=register_form.clean_password2())
                if authenticated_user is not None:
                    auth_login(self.request, authenticated_user)
                    return redirect(reverse_lazy('choice'))
            else:
                print(register_form.errors)
                return self.render_to_response(self.get_context_data(register_form=register_form))

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'register_form': UserRegistrationForm()}
        context.update(super().get_context_data(**kwargs))

        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user is not None:
            auth_login(self.request, user)
        else:
            return self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        form.add_error(None, "Неверный email или пароль")
        return self.render_to_response(self.get_context_data(form=form))


class SelectUserTypeView(FormView):
    form_class = UserTypeSelectionForm
    template_name = 'auth/auth_choice.html'
    success_url = reverse_lazy('view_profile')  

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            user_profile = self.request.user 
            user_profile.user_type = form.cleaned_data['user_type']
            print(form.cleaned_data['user_type'])
            user_profile.save()
            if user_profile.user_type == 'provider':
                Provider.objects.get_or_create(user=user_profile, is_provider=True)
            elif user_profile.user_type == 'buyer':
                Provider.objects.get_or_create(user=user_profile, is_provider=False)
        return super().form_valid(form)


class LogoutView(RedirectView):
    url = '/'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class ViewProfile(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    template_name = 'auth/profile.html'
    success_url = reverse_lazy('view_profile')

    def get_object(self):
        return self.request.user


@login_required
def login_redirect(request):
    if not request.user.user_type:  
        return redirect('/select_user_type/')
    else:
        return redirect('/profile/')


class SelectAuthUserTypeView(FormView):
    form_class = UserTypeSelectionForm
    template_name = 'auth/cabinet_choice.html'
    success_url = reverse_lazy('view_profile')

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.user_type:
            return redirect(reverse_lazy('view_profile'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            user_profile = self.request.user
            user_profile.user_type = form.cleaned_data['user_type']
            print(form.cleaned_data['user_type'])
            user_profile.save()
            if user_profile.user_type == 'provider':
                Provider.objects.get_or_create(user=user_profile)
            elif user_profile.user_type == 'buyer':
                Buyer.objects.create(user=user_profile)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contacts = Contacts.load()
        context['contacts'] = contacts
        return context


def cabinet_create(request):
    try:
        cabinet = request.user.cabinet
    except ObjectDoesNotExist:
        cabinet = Cabinet.objects.create(user=request.user)
    return redirect(reverse_lazy('choice'))
