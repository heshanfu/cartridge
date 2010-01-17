
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from shop.models import Category, Product, ProductVariation, Order, OrderItem
from shop.fields import MoneyField
from shop import forms


# lists of field names
option_fields = [field.name for field in ProductVariation.option_fields()]
image_fields = [field.name for field in Product.image_fields()]
billing_fields = Order.billing_detail_field_names()
shipping_fields = Order.shipping_detail_field_names()

		
class CategoryAdmin(admin.ModelAdmin):
	ordering = ("parent", "title")
	list_display = ("title", "parent", "active", "admin_link")
	list_editable = ("parent", "active")
	list_filter = ("parent",)
	search_fields = ("title", "parent__title", "product_set__title")	

class ProductVariationAdmin(admin.TabularInline):
	verbose_name_plural = _("Current variations")
	model = ProductVariation
	fields = ("sku", "default", "quantity", "unit_price", "sale_price", 
		"sale_from", "sale_to")
	extra = 0
	formset = forms.ProductVariationAdminFormset
	
class ProductAdmin(admin.ModelAdmin):

	list_display = ("title", "active", "available", "admin_link")
	list_editable = ("active", "available")
	list_filter = ("categories", "active", "available")
	filter_horizontal = ("categories",)
	search_fields = ("title", "categories__title", "variations_sku")
	inlines = (ProductVariationAdmin,)
	form = forms.ProductAdminForm
	formfield_overrides = {MoneyField: {"widget": forms.MoneyWidget}}

	fieldsets = (
		(None, {"fields": 
			("title", "description", ("active", "available"), "categories")}),
		(_("Images"), {"fields": image_fields}),
		(_("Create new variations"), {"fields": option_fields}),
	)

	def save_model(self, request, obj, form, change):
		"""
		store the product object for creating variations in save_formset
		"""
		super(ProductAdmin, self).save_model(request, obj, form, change)
		self._product = obj

	def save_formset(self, request, form, formset, change):
		"""
		create variations for selected options if they don't exist, and also
		manage the default empty variation, creating it if no variations exist 
		or removing it if multiple variations exist 
		"""
		super(ProductAdmin, self).save_formset(request, form, formset, change)
		options = dict([(f, request.POST.getlist(f)) for f in option_fields 
			if request.POST.getlist(f)])
		self._product.variations.create_from_options(options)
		self._product.variations.manage_empty()

class OrderItemInline(admin.TabularInline):
	verbose_name_plural = _("Items")
	model = OrderItem
	extra = 0

class OrderAdmin(admin.ModelAdmin):

	ordering = ("status", "-id")
	list_display = ("id", "billing_name", "total", "time", "status")
	list_editable = ("status",)
	list_filter = ("status", "time")
	list_display_links = ("id", "billing_name",)
	search_fields = ["id", "status"] + billing_fields + shipping_fields
	date_hierarchy = "time"
	radio_fields = {"status": admin.HORIZONTAL}
	inlines = (OrderItemInline,)
	formfield_overrides = {MoneyField: {"widget": forms.MoneyWidget}}
	fieldsets = (
		(_("Billing details"), {"fields": (tuple(billing_fields),)}),
		(_("Shipping details"), {"fields": (tuple(shipping_fields),)}),
		(None, {"fields": ("additional_instructions", ("shipping_total", 
			"shipping_type"), "item_total",("total", "status"))}),
	)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)

