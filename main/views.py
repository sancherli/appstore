from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST
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
from django.urls import reverse_lazy, reverse

from django.views.generic import TemplateView, ListView, DetailView

from .models import App, Category
from .forms import ReviewForm, AppForm, RegisterForm, ForSuperUserEditAppForm

SORTS = {
    'new': '-created_at',
    'name': 'name',
    'price': 'price',
    'expensive': '-price',
}


def index(request):
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', 'new')

    if q:
        apps = App.objects.filter(Q(name__icontains=q) | Q(description__icontains=q))
    else:
        apps = App.objects.all()

    apps = apps.select_related('author')
    if sort == 'rating':
        apps = apps.order_by('-rating_avg', '-rating_count', 'name')
    else:
        apps = apps.order_by(SORTS.get(sort, '-created_at'))

    featured = App.objects.order_by('-price').first()

    paginator = Paginator(apps, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'main/index.html', {
        'q': q,
        'sort': sort,
        'page_obj': page_obj,
        'featured': featured,
    })

# @require_GET
# def about(request):
#     return render(request, 'main/about.html')


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
        context['similar_apps'] = app.similar_by_price()
        form = ReviewForm()
        if self.request.user.is_authenticated and 'username' in form.fields:
            form.fields.pop('username')
        context['form'] = form
        context['reviews'] = app.review_set.order_by('-created_at')
        context['is_favorite'] = (
            self.request.user.is_authenticated
            and app.favorited_by.filter(pk=self.request.user.pk).exists()
        )
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
        return redirect(app.get_absolute_url())

    if request.user.is_authenticated and 'username' in form.fields:
        form.fields.pop('username')
    reviews = app.review_set.order_by('-created_at')
    similar_apps = app.similar_by_price()
    return render(request, 'main/app_detail.html', {
        'app': app,
        'form': form,
        'reviews': reviews,
        'similar_apps': similar_apps,
        'is_favorite': request.user.is_authenticated
                       and app.favorited_by.filter(pk=request.user.pk).exists()
    })


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    apps = App.objects.filter(category=category)
    return render(request, 'main/category.html', {
        'category': category,
        'apps': apps,
    })


# def new(request):
#     apps = App.objects.order_by('-created_at')[:5]
#     return render(request, 'main/new.html', {'apps': apps})


class NewAppView(ListView):
    model = App
    template_name = 'main/new.html'
    context_object_name = 'apps'
    ordering = ['-created_at']
    paginate_by = 3


# def apps_list(request, is_free):
#     if is_free:
#         apps = App.objects.filter(price=0)
#         title = 'Бесплатные приложения'
#     else:
#         apps = App.objects.filter(price__gt=0)
#         title = 'Платные приложения'
#
#     return render(request, 'main/apps_list.html', {
#         'apps': apps,
#         'title': title,
#     })


class AppsIsFreeListView(ListView):
    model = App
    template_name = 'main/apps_list.html'
    context_object_name = 'apps'

    def get_queryset(self):
        if self.kwargs.get('is_free'):
            return App.objects.filter(price=0)
        return App.objects.filter(price__gt=0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get('is_free'):
            context['title'] = 'Бесплатные приложения'
        else:
            context['title'] = 'Платные приложения'
        return context


def api_app_detail(request, app_id):
    app = get_object_or_404(App, id=app_id)
    data = {
        'id': app.id,
        'name': app.name,
        'description': app.description,
        'price': app.price,
    }
    return JsonResponse(data)


@login_required
def add_app(request):
    if request.method == 'POST':
        form = AppForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.author = request.user
            app.save()
            messages.success(request, f"Приложение {app.name} опубликовано")
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
def edit_app(request, app_id):
    app = get_object_or_404(App, id=app_id)
    if not (
        request.user.has_perm('main.change_app')
        or request.user.is_staff
        or app.author_id == request.user.id
    ):
        print('1')
        messages.error(request, 'Редактировать карточку приложения может только его автор!')
        return redirect('main:app_detail', app_id=app.id)

    if request.method == "POST":
        if request.user.is_superuser:
            form = ForSuperUserEditAppForm(request.POST, request.FILES, instance=app)
        else:
            form = AppForm(request.POST, request.FILES, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, f"Карточка приложения {app.name} изменена")
            return redirect('main:app_detail', app_id=app.id)

    else:
        if request.user.is_superuser:
            form = ForSuperUserEditAppForm(instance=app)
        else:
            form = AppForm(instance=app)

    return render(request, 'main/edit_app.html', {'form': form, 'app': app})


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


@login_required
def favorites(request):
    apps = request.user.favorite_apps.select_related('category', 'author').order_by('name')
    return render(request, 'main/favorites.html', {'apps': apps})


@require_POST
def toggle_favorite(request, app_id):
    app = get_object_or_404(App, id=app_id)

    if not request.user.is_authenticated:
        login_url = reverse('main:login')
        next_url = reverse(app.get_absolute_url())
        return redirect(f"{login_url}?next={next_url}")

    if app.favorited_by.filter(pk=request.user.pk).exists():
        app.favorited_by.remove(request.user)
        messages.success(request, f"{app.name} - убрано из избранного")

    else:
        app.favorited_by.add(request.user)
        messages.success(request, f"{app.name} - добавили в избранное")

    return redirect('main:app_detail', app_id=app.id)


@login_required
def sale(request):
    if not request.user.is_staff:
        messages.error(request, 'Распродажу запускает только сотрудник магазина.')
        return redirect('main:index')

    if request.method == 'POST':
        updated = App.discount_paid(10)
        messages.success(
            request,
            f'Скидка 10% применена к платным приложениям: {updated}.',
        )
        return redirect('main:index')

    paid_count = App.objects.filter(price__gt=0).count()
    return render(request, 'main/sale.html', {'paid_count': paid_count})


def menu(request):
    categories = Category.objects.filter(is_visible=True)
    return {
        'categories': categories,
    }
