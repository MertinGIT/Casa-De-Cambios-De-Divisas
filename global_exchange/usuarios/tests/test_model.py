from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserModelTest(TestCase):

    def test_creacion_usuario_valido(self):
        """Debe poder crearse un usuario con username, email, cedula y password"""
        user = User.objects.create_user(
            username="juan",
            email="juan@example.com",
            cedula="123456",
            password="Testpass123!"
        )
        self.assertEqual(user.username, "juan")
        self.assertEqual(user.email, "juan@example.com")
        self.assertEqual(user.cedula, "123456")
        self.assertTrue(user.check_password("Testpass123!"))

    def test_username_unico(self):
        """El username debe ser único"""
        User.objects.create_user(
            username="pepe",
            email="pepe@example.com",
            cedula="111",
            password="pass1234"
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="pepe",
                email="otro@example.com",
                cedula="222",
                password="pass1234"
            )

    def test_cedula_unica(self):
        """La cédula debe ser única"""
        User.objects.create_user(
            username="user1",
            email="user1@example.com",
            cedula="12345",
            password="pass1234"
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="user2@example.com",
                cedula="12345",  # repetida
                password="pass1234"
            )

    def test_cedula_no_puede_ser_vacia(self):
        """La cédula no puede ser vacía"""
        user = User(username="test", email="test@example.com", cedula="")
        with self.assertRaises(ValidationError):
            user.full_clean()  # dispara validaciones de modelo

    def test_str_retorna_username(self):
        """__str__ debe devolver el username"""
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            cedula="55555",
            password="pass1234"
        )
        self.assertEqual(str(user), "maria")
