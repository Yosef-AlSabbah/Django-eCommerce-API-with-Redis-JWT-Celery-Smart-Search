from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, UserAccount


# Extend the base UserAdmin to customize for UserAccount
@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    """
    Admin view for the UserAccount model with enhanced visibility and control over user details.
    """
    # Fields to display in the user list
    list_display = ('id', 'email', 'username', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_manager', 'is_admin')

    # Fields to enable search by email and username
    search_fields = ('email', 'username')

    # Fields layout in the detail view
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'bio', 'profile_image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_manager', 'is_admin')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('groups', 'user_permissions'),
        }),
    )

    # Fields layout when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name', 'phone_number', 'password1', 'password2', 'is_active',
                'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')

    # Ensure email and username are used for logging in and user identification
    ordering = ('email',)

    def has_add_permission(self, request):
        """
        Control add permissions if needed.
        """
        return True

    def has_change_permission(self, request, obj=None):
        """
        Allow edits only for staff members.
        """
        if request.user.is_staff:
            return True
        return False


# Register the ProfileAdmin as well
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin view for the Profile model with limited edit permissions.
    """
    list_display = ('user', 'balance', 'date_created')
    search_fields = ('user__username', 'user__email')  # Use 'username' and 'email' instead of 'name'

    readonly_fields = ('balance', 'date_created')  # Make balance and date_created read-only

    def get_form(self, request, obj=None, **kwargs):
        """Customize form to limit user choices and enforce creation-only permissions."""
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            # Restrict user choices to those without a profile only during creation
            form.base_fields['user'].queryset = UserAccount.objects.filter(profile__isnull=True)
        else:
            # Make the user field read-only when viewing an existing profile
            self.readonly_fields = ('user', 'balance', 'date_created')
        return form

    def has_change_permission(self, request, obj=None):
        """
        Allow profile creation but restrict editing after creation.
        """
        if obj is not None:
            return False  # Disable editing of existing profiles
        return True
