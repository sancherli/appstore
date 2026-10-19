from http.client import responses

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
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

from .models import App, Category, Review, Purchase
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
        context['purchase'] = app.purchase_of(self.request.user)
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
                       and app.favorited_by.filter(pk=request.user.pk).exists(),
        'purchase': app.purchase_of(request.user),
    })


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    apps = App.objects.filter(category=category).defer('description')
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
    paginate_by = 3

    def get_queryset(self):
        return App.objects.newest()


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
            return App.objects.free()
        return App.objects.paid()

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
        next_url = app.get_absolute_url()
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
        messages.error(request, 'Распродажу запускает только персонал')
        return redirect('main:index')

    if request.method == 'POST':
        updated = App.discount_paid(10)
        messages.success(request, f'Скидка 10% применена к платным приложениям: {updated}')
        return redirect('main:index')

    paid_count = App.objects.paid().count()
    return render(request, 'main/sale.html', {'paid_count': paid_count})


@login_required
def close_category(request, category_id):
    source = get_object_or_404(Category, id=category_id)
    if not request.user.is_staff:
        messages.error(request, 'Категорию может закрыть только сотрудник магазина')
        return redirect('main:index')

    targets = Category.objects.exclude(pk=source.pk).order_by('name')
    if request.method == 'POST':
        raw_target = request.POST.get('target_id', '')
        if not str(raw_target).isdigit():
            messages.error(request, 'Выберите категорию в которую перенести приложения')
            return redirect('main:close_category', category_id=source.pk)
        target = get_object_or_404(Category, id=int(raw_target))
        try:
            moved = App.objects.move_to_category(source, target)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('main:close_category', category_id=source.pk)
        messages.success(request, f'Категория закрыта. Перенесены приложения: {moved}')
        return redirect('main:category', category_id=target.pk)

    apps_count = App.objects.in_category(source).count()
    return render(request, 'main/close_category.html', {
        'source': source,
        'targets': targets,
        'apps_count': apps_count,
    })


@require_POST
def buy_app(request, app_id):
    app = get_object_or_404(App, id=app_id)

    if not request.user.is_authenticated:
        login_url = reverse('main:login')
        return redirect(f"{login_url}?next={app.get_absolute_url()}")

    if app.author_id == request.user.id:
        messages.error(request, 'Это ваше приложение, покупать его вам не нужно')
        return redirect(app.get_absolute_url())

    if app.purchase_of(request.user) is not None:
        messages.info(request, f'{app.name} уже есть в ваших покупках')
        return redirect(app.get_absolute_url())

    app.buyers.add(request.user, through_defaults={'price_paid': app.price})
    messages.success(request, f"Покупка оформлена: {app.name}, {app.price_label()}")
    return redirect(app.get_absolute_url())


@login_required
def purchases(request):
    items = (
        Purchase.objects.filter(user=request.user)
        .select_related('app')
        .only('price_paid', 'purchased_at', 'app__name', 'app__price')
        .order_by('-purchased_at')
    )
    total = items.aggregate(total=Sum('price_paid'))['total'] or 0
    return render(request, 'main/purchases.html', {
        'purchases': items,
        'total': total,
    })