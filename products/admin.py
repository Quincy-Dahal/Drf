"""
products/admin.py

"""

from django.contrib import admin

from .models import Product, ProductCategory, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "display_order", "is_active", "price_range_display")
    list_editable = ("display_order",)
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    inlines = [ProductVariantInline]


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)