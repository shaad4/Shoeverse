from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        Map Google data to your User model
        """
        user = super().populate_user(request, sociallogin, data)

        # Google fields
        full_name = data.get("name")
        first_name = data.get("given_name")
        last_name = data.get("family_name")

        # ✅ Set fullName (your custom field)
        user.fullName = (
            full_name
            or f"{first_name} {last_name}".strip()
            or first_name
            or "Google User"
        )

        return user
