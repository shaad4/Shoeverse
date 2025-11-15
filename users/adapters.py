from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.files.base import ContentFile
import requests

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        """
        Populate custom fields before saving the user 
        (full name, email, etc.)
        """
        user = super().populate_user(request, sociallogin, data)

        # Google fields
        full_name = data.get("name")
        first_name = data.get("given_name")
        last_name = data.get("family_name")

        # ⭐ Correct fullName logic (NO "None None")
        if full_name:
            user.fullName = full_name

        elif first_name or last_name:
            user.fullName = f"{first_name or ''} {last_name or ''}".strip()

        else:
            # fallback
            user.fullName = user.email.split("@")[0]

        return user


    def save_user(self, request, sociallogin, form=None):
        """
        After the user object is created, save extra fields like profile image.
        """
        user = super().save_user(request, sociallogin, form)

        extra = sociallogin.account.extra_data

        # Google profile picture
        picture_url = extra.get("picture")

        if picture_url:
            try:
                response = requests.get(picture_url)
                if response.status_code == 200:
                    user.profileImage.save(
                        f"{user.id}_google.jpg",
                        ContentFile(response.content),
                        save=True
                    )
            except Exception:
                pass

        return user
