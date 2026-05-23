from django.db import models


class BasicUserModel(models.Model):
    def __init__(
        self,
        surname,
        name,
        email,
        phone_number,
        birth_date,
        social_security_number,
        role,  # to see if its a provider or a customer
    ):
        pass
