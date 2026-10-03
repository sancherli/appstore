from ast import Store
from http.client import responses
from django.db.models.fields import return_None
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse,HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import TemplateView, ListView, DetailView

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm

from .models import App, Category, Review
from .forms import ReviewForm, AppForm, RegisterForm, AppEditForm, ForSuperUserEditAppForm
from django.http import HttpResponseForbidden


SORTS = {
    'new': '-created_at',
    'name': 'name',
    'price': 'price',
    'expensive': '-price',
}

@require_GET
def about(request):
    return render(request, 'main/about.html')


class NewAppsView(ListView):
    model = App
    template_name = 'main/new.html'
    context_object_name = 'apps'
    ordering = ['-created_at']
    paginate_by = 5

class AppDetailView(DetailView):
    model = App
    template_name = 'main/app_detail.html'
    context_object_name = 'app'
    pk_url_kwarg = 'app_id'


class IndexView(TemplateView):
    template_name = 'main/index.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['apps'] = App.objects.all()
        context['categories'] = Category.objects.all()
        context['featured'] = App.objects.order_by('-price').first()

        return context


def index(request):
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', 'new')
    if q:
        apps = App.objects.filter(Q(name__icontains=q) | Q(description__icontains=q))
    else:
        apps = App.objects.all()
    apps = apps.select_related('author').order_by(SORTS.get(sort, '-created_at'))
    featured = App.objects.order_by('-price').first()
    categories = Category.objects.all()
    paginator = Paginator(apps, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'main/index.html', {
        'q': q,
        'sort': sort,
        'page_obj': page_obj,
        'featured': featured,
    })

def reviews(request):
    reviews = Review.objects.all()
    return render(request, 'main/reviews.html', {
        'reviews': reviews
    })


class AboutView(TemplateView):
    template_name = 'main/about.html'


# def app_detail(request, app_id):
#     app = get_object_or_404(App, id=app_id)
#     return render(request, 'main/app_detail.html', {'app': app})

class AppDetailView(DetailView):
    model = App
    template_name = 'main/app_detail.html'
    context_object_name = 'app'
    pk_url_kwarg = 'app_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app = self.object
        context['similar_apps'] = App.objects.filter(
            price__gte=app.price - 30,
            price__lte=app.price + 30
        ).exclude(
            id=app.id
        )[:3]
        context['form'] = ReviewForm()
        context['reviews'] = app.review_set.order_by('-created_at')
        return context


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    apps = App.objects.filter(category=category)
    most_expensive = apps.order_by('-price').first()
    return render(request, 'main/category.html', {
        'category': category,
        'apps': apps,
        'most_expensive': most_expensive,
    })

def app_detail(request, app_id, slug):
    app = get_object_or_404(App, id=app_id)
    similar_by_price = App.objects.filter(
        price__gte=app.price - 30,
        price__lte=app.price + 30
    ).exclude(id=app.id)[:3]
    return render(request, 'main/app_detail.html', {
        'app': app,
        'similar_by_price': similar_by_price,
    })


def new(request):
    apps = App.objects.order_by('-created_at')[:5]
    return render(request, 'main/new.html', {'apps': apps})


def archive_year(request, year):
    return HttpResponse(f"Вы открыли архив за {year} год")


class AppsDetailView(DetailView):
    model = App
    template_name = 'main/app_detail.html'
    context_object_name = 'app'
    pk_url_kwarg = 'app_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app = self.object

        context['similar_apps'] = App.objects.filter(
            price__gte=app.price - 30,
            price__lte=app.price + 30
        ).exclude(
            id=app.id
        )[:3]
        form = ReviewForm()
        if self.request.user.is_authenticated and 'username' in form.fields:
            form.fields.pop('username')
        context['form'] = form
        context['reviews'] = app.review_set.order_by('-created_at')
        return context


@require_POST
def add_review(request, app_id):
    app = get_object_or_404(App, id=app_id)
    data = request.POST.copy()
    if request.user.is_authenticated:
        data['username'] = request.user.username
    form = ReviewForm(data)

    if form.is_valid():
        review = form.save(commit=False)
        review.app = app
        review.save()
        messages.success(request, 'Отзыв сохранён.')
        return redirect('main:app_detail',app_id=app.id,slug=app.slug)

    if request.user.is_authenticated and 'username' in form.fields:
        form.fields.pop('username')
    reviews = app.review_set.order_by('-created_at')
    similar_apps = (
        App.objects.filter(
            price__gte=app.price - 10,
            price__lte=app.price + 10,
        )
        .exclude(id=app.id)[:3]
    )
    return render(request, 'main/app_detail.html', {
        'app': app,
        'form': form,
        'reviews': reviews,
        'similar_apps': similar_apps,
    })



def no_category(request):
    apps = App.objects.filter(category=None)
    return render(request, 'main/no_category.html', {
        'apps': apps
    })


def free_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    apps = App.objects.filter(
        category=category,
        price=0
    )
    return render(request, 'main/free_by_category.html', {
        'category': category,
        'apps': apps
    })


def cheap_apps(request):
    apps = App.objects.filter(
        price__gt=0,
        price__lt=100
    ).order_by('price')
    return render(request, 'main/cheap.html', {
        'apps': apps
    })

def top_apps(request):
    apps = App.objects.filter(price__gt=0).order_by('-price')[:10]
    return render(request, 'main/top.html', {
        'apps': apps
    })

def api_app_detail(request, app_id):
    app = get_object_or_404(App, id=app_id)
    return JsonResponse({
        'id': app.id,
        'name': app.name,
        'description': app.description,
        'price': str(app.price),
        'icon': app.icon.url if app.icon else None,
    })


class AppsListView(ListView):
    model = App
    template_name = 'main/app_list.html'
    context_object_name = 'apps'

    def get_queryset(self):
        is_free = self.kwargs.get('is_free')

        if is_free:
            return App.objects.filter(price=0)

        return App.objects.filter(price__gt=0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.kwargs.get('is_free'):
            context['title'] = 'Бесплатные приложения'
        else:
            context['title'] = 'Платные приложения'

        return context


@login_required
def add_app(request):
    if request.method == 'POST':
        form = AppForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.author = request.user
            app.save()
            messages.success(request, f'Приложение «{app.name}» опубликовано.')
            return redirect('main:app_detail', app_id=app.id)
    else:
        form = AppForm()
    return render(request, 'main/add_app.html', {'form': form})



def register(request):
    if request.user.is_authenticated:
        return redirect('main:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Аккаунт создан.')
            return redirect('main:index')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


class StoreLoginView(LoginView):
    template_name = 'main/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'С возвращением, {self.request.user.username}!')
        return response

class StoreLogoutView(LogoutView):
    next_page = reverse_lazy('main:index')


@login_required
def my_apps(request):
    apps = App.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'main/my_apps.html', {'apps': apps})



@login_required
def edit_apps(request, app_id):
    app = get_object_or_404(App, id=app_id)
    if not request.user.is_staff and app.author_id != request.user.id:
        messages.error(request, 'Редактировать карточку может только её автор.')
        return redirect('main:app_detail',app_id=app.id,slug=app.slug)

    if request.method == 'POST':
        form = AppForm(request.POST, request.FILES, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, f'Карточка «{app.name}» обновлена.')
            return redirect('main:app_detail',app_id=app.id,slug=app.slug)
    else:
        form = AppForm(instance=app)
    return render(request, 'main/edit_app.html', {'form': form, 'app': app})


@login_required
def edit_apps(request, app_id):
    app = get_object_or_404(App, id=app_id)
    if not (
        request.user.has_perm('main.change_app')
        or request.user.is_staff
        or app.author_id == request.user.id
    ):
        messages.error(request,'Редактировать карточку может только её автор.')
        return redirect('main:app_detail',app_id=app.id,slug=app.slug,)
    if request.method == 'POST':
        if request.user.is_superuser:
            form = ForSuperUserEditAppForm(request.POST,request.FILES,instance=app,)
        else:
            form = AppForm(request.POST,request.FILES,instance=app,)
        if form.is_valid():
            app = form.save()
            messages.success(request,f'Карточка приложения {app.name} изменена')
            return redirect('main:app_detail',app_id=app.id,slug=app.slug,)
    else:
        if request.user.is_superuser:
            form = ForSuperUserEditAppForm(instance=app)
        else:
            form = AppForm(instance=app)
    return render(request,'main/edit_app.html',{'form': form,'app': app,})

class StorePasswordResetView(PasswordResetView):
    template_name = 'main/password_reset_form.html'
    email_template_name = 'main/password_reset_email.html'
    subject_template_name = 'main/password_reset_subject.txt'
    success_url = reverse_lazy('main:password_reset_done')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['email'].label = 'Электронная почта'
        return form


class StorePasswordResetDoneView(PasswordResetDoneView):
    template_name = 'main/password_reset_done.html'


class StorePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'main/password_reset_confirm.html'
    success_url = reverse_lazy('main:password_reset_complete')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form is not None and 'new_password1' in form.fields:
            form.fields['new_password1'].label = 'Новый пароль'
            form.fields['new_password2'].label = 'Повтор пароля'
        return form


class StorePasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'main/password_reset_complete.html'

