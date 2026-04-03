import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver


@receiver(social_account_added)
@receiver(social_account_updated)
def save_google_profile(request, sociallogin, **kwargs):
    user = sociallogin.user

    if sociallogin.account.provider == 'google':
        extra_data = sociallogin.account.extra_data
        picture_url = extra_data.get('picture')

        # Only save if not already set
        if picture_url and not user.profile_image:
            try:
                response = requests.get(picture_url)
                if response.status_code == 200:
                    file_name = f"{user.username}_google.jpg"
                    user.profile_image.save(
                        file_name,
                        ContentFile(response.content),
                        save=True
                    )
            except Exception as e:
                print("Error saving profile image:", e)