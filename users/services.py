import os
import stripe
from django.conf import settings
from django.db.models import Sum
from users.models import Payment
from materials.models import Course, Lesson

# Устанавливаем секретный ключ Stripe из переменных окружения
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def create_stripe_product(name: str):
    """
        Создаёт продукт в Stripe
            Аргументы:
                name (str):Название продукта.
            Возвращает:
                stripe.Product: Объект продукта Stripe.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при создании продукта.
    """
    try:
        product = stripe.Product.create(
            name=name,
        )
        return product
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании продукта Stripe: {e}")
        raise


def create_stripe_price(amount: int, product_id: str):
    """
        Создает цену для продукта в Stripe.
            Аргументы:
                amount (int): Сумма в минимальных единицах валюты (например, в копейках для рублей).
                product_id (str): ID продукта Stripe, к которому привязывается цена.
            Возвращает:
                stripe.Price: Объект цены Stripe.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при создании цены.
    """
    try:
        price = stripe.Price.create(
            currency="rub",  # Валюта - рубли. Можно изменить на "usd" или другую.
            unit_amount=amount,  # Сумма в копейках (умножаем на 100)
            product_data={"name": "Платный материал"},  # Обязательное поле, даже если есть product_id
            lookup_keys=['sample_price'],
            transfer_lookup_key=True
        )
        return price
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании цены Stripe: {e}")
        raise


def create_stripe_checkout_session(price_id: str, payment_id: int):
    """
        Создает сессию Stripe Checkout для получения ссылки на оплату.
            Аргументы:
                price_id (str): ID цены Stripe.
                payment_id (int): ID платежа в вашей системе (для метаданных).
            Возвращает:
                stripe.checkout.Session: Объект сессии Stripe Checkout.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при создании сессии.
    """
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=settings.BASE_URL + "/success?session_id={CHECKOUT_SESSION_ID}",  # URL для успешной оплаты
            cancel_url=settings.BASE_URL + "/cancel",  # URL для отмены оплаты
            metadata={"payment_id": payment_id},  # Сохраняем ID нашего платежа
        )
        return checkout_session
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании сессии Stripe Checkout: {e}")
        raise


def retrieve_stripe_session(session_id: str):
    """
        Получает информацию о сессии Stripe по ее ID.
            Аргументы:
                session_id (str): ID сессии Stripe.
            Возвращает:
                stripe.checkout.Session: Объект сессии Stripe Checkout.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при получении сессии.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session
    except stripe.error.StripeError as e:
        print(f"Ошибка при получении сессии Stripe: {e}")
        raise


def process_payment_and_create_stripe_session(user, paid_course_id, paid_lesson_id):
    """
        Обрабатывает запрос на оплату, создает запись Payment и генерирует сессию Stripe.
            Аргументы:
                user (User): Пользователь, совершающий оплату.
                paid_course_id (int): ID курса для оплаты (может быть None).
                paid_lesson_id (int): ID урока для оплаты (может быть None).
            Возвращает:
                dict: Словарь с информацией о платеже и ссылкой на оплату.
            Исключения:
                ValueError: Если не указан ни курс, ни урок, или оба.
                Http404: Если курс или урок не найден.
                stripe.error.StripeError: Если произошла ошибка при взаимодействии со Stripe.
    """
    if paid_course_id and paid_lesson_id:
        raise ValueError("Платеж не может быть одновременно за курс и за урок.")
    if not paid_course_id and not paid_lesson_id:
        raise ValueError("Платеж должен быть связан либо с курсом, либо с уроком.")

    item_title = ""
    amount_to_pay = 0

    if paid_course_id:
        try:
            course = Course.objects.get(pk=paid_course_id)
            item_title = course.title
            # Суммируем стоимости всех уроков в курсе
            amount_to_pay = course.lessons.aggregate(total_amount=Sum('price'))['total_amount'] or 0
        except Course.DoesNotExist:
            raise ValueError("Курс не найден.")
    elif paid_lesson_id:
        try:
            lesson = Lesson.objects.get(pk=paid_lesson_id)
            item_title = lesson.title
            amount_to_pay = lesson.price
        except Lesson.DoesNotExist:
            raise ValueError("Урок не найден.")

    if amount_to_pay <=0:
        raise ValueError("Сумма оплаты должна быть больше нуля.")

    # Создаём запись платежа в вашей системе со статусом pending
    payment = Payment.objects.create(
        user=user,
        paid_course_id=paid_course_id,
        paid_lesson_id=paid_lesson_id,
        amount=amount_to_pay,
        payment_method="stripe",
        status="pending",
    )

    try:
        # Создаем продукт в Stripe
        stripe_product = create_stripe_product(item_title)

        # Создаем цену в Stripe (сумма в копейках)
        stripe_price = create_stripe_price(int(amount_to_pay * 100), stripe_product.id)

        # Создаем сессию оплаты Stripe
        checkout_session = create_stripe_checkout_session(stripe_price.id, payment.id)

        # Обновляем запись платежа в вашей системе
        payment.stripe_id = checkout_session.id
        payment.payment_url = checkout_session.url
        payment.save()

        return {
            "payment_id": payment.id,
            "payment_url": checkout_session.url,
            "amount": payment.amount,
            "status": payment.status,
            "message": "Сессия оплаты успешно создана.",
        }
    except stripe.error.StripeError as e:
        # Если произошла ошибка Stripe, устанавливаем статус платежа как "failed"
        payment.status = "failed"
        payment.save()
        raise ValueError(f"Ошибка Stripe при создании платежа: {e}")
