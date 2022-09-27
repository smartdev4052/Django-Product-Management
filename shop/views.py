from django.shortcuts import redirect, render, get_object_or_404
from shop.forms import ProductCreateForm
from django.contrib.auth.decorators import user_passes_test
from shop.models import Category, Product
from django.utils.translation import ugettext_lazy as _

# SHOP


def shop_index_view(request):
    context = {}
    products = Product.objects.all()
    context['products'] = products
    return render(request, 'shop/index.html', context)


def shop_detail_view(request, slug):
    context = {}
    product = get_object_or_404(Product, slug=slug)
    products = Product.objects.exclude(slug=slug)[0:5]
    context['product'] = product
    context['products'] = products
    return render(request, 'shop/detail.html', context)


def shop_category_view(request):
    categories = Category.objects.all()
    context = {}
    context['categories'] = categories
    return render(request, 'shop/category.html', context)


def shop_by_category_view(request, slug):
    category = Category.objects.filter(slug=slug).first()
    products = Product.objects.filter(category__slug=slug)
    context = {}
    context['products'] = products
    context['category'] = category
    return render(request, 'shop/by_category.html', context)

# PRODUCT


def product_index_view(request):
    context = {}
    products = Product.objects.all()
    context['products'] = products
    return render(request, 'product/index.html', context)


def product_detail_view(request, slug):
    context = {}
    product = get_object_or_404(Product, slug=slug)
    context['product'] = product
    return render(request, 'product/detail.html', context)

# Superuser


@user_passes_test(lambda u: u.is_superuser)
def product_create_view(request):
    if request.method == 'POST':
        form = ProductCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop:product_index')
    else:
        form = ProductCreateForm()
    return render(request, 'product/create.html', {'form': form})


# Superuser
@user_passes_test(lambda u: u.is_superuser)
def product_edit_view(request, slug):
    product = get_object_or_404(Product,  slug=slug)
    if request.method == 'POST':
        form = ProductCreateForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('shop:product_index')
    else:
        form = ProductCreateForm(instance=product)
    return render(request, 'product/edit.html', {'form': form})

# Superuser


@user_passes_test(lambda u: u.is_superuser)
def product_delete_view(request, slug):
    Product.objects.filter(slug=slug).delete()
    context = {}
    return redirect('shop:product_index')
