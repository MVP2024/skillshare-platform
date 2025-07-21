import os
import stripe
from django.conf import settings
from django.db.models import Sum
from users.models import Payment
from materials.models import Course, Lesson
from django.shortcuts import get_object_or_404

# Устанавливаем секретный ключ Stripe из переменных окружения
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def create_stripe_product(name: str):
    """
        Создаёт продукт в Stripe
            Аргументы:
                name (str):Название продукта.
                    Если продукт с таким именем уже существует, используется существующий.
                    В противном случае создается новый продукт.
            Возвращает:
                stripe.Product: Объект продукта Stripe.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при взаимодействии со Stripe API.
    """
    try:
        # Попытаться найти существующий продукт по имени
        # Параметр 'name' в stripe.Product.list может вызывать ошибку "unknown parameter"
        # в некоторых версиях API или конфигурациях.
        # Для больших объемов данных рекомендуется хранить Stripe ID продукта в вашей базе.

        all_products = stripe.Product.list(active=True, limit=100)  # Увеличьте limit, если у вас много продуктов
        for product in all_products.data:
            if product.name == name:
                print(f"Продукт '{name}' уже существует, используем его.")
                return product

        # Если продукт не найден, создать новый
        product = stripe.Product.create(
            name=name,
            active=True,  # Убедитесь, что продукт активен
        )
        return product
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании/получении продукта Stripe: {e}")
        raise


def create_stripe_price(amount: int, stripe_product_id: str, lookup_key: str):
    """
        Создает или находит цену для продукта в Stripe.
        Цены в Stripe неизменяемы, поэтому при изменении суммы для существующего product_id
        или lookup_key, необходимо создать новую цену.
            Аргументы:
                amount (int): Сумма в минимальных единицах валюты (например, в копейках для рублей).
                Сумма должна быть уже умножена на 100 перед передачей.
                stripe_product_id (str): ID продукта Stripe, к которому привязывается цена.
                lookup_key (str): Уникальный ключ для быстрого поиска цены.
                                Рекомендуется включать в него ID продукта и сумму для уникальности.
            Возвращает:
                stripe.Price: Объект цены Stripe.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при создании/получении цены.
    """
    try:
        # Попытаться найти существующую цену по lookup_key и product_id
        # Это гарантирует, что мы найдем точную цену, если она уже существует.
        existing_prices = stripe.Price.list(
            lookup_keys=[lookup_key],
            product=stripe_product_id,
            unit_amount=amount,  # Добавлено для точного соответствия суммы
            currency="rub",  # Добавлено для точного соответствия валюты
            active=True  # Учитывать только активные цены
        )
        if existing_prices.data:
            print(
                f"Цена с lookup_key '{lookup_key}', суммой {amount / 100.0:.2f} и продуктом '{stripe_product_id}' уже существует, используем её.")
            return existing_prices.data[0]  # Вернуть первую найденную цену

        # Если цена не найдена, создать новую
        price = stripe.Price.create(
            currency="rub",  # Валюта - рубли. Можно изменить на "usd" или другую.
            unit_amount=amount,  # Сумма в копейках (умножаем на 100)
            product=stripe_product_id,  # Используем ID существующего продукта
            lookup_key=lookup_key,  # Используем динамический lookup_key
            active=True,
        )
        return price
    except stripe.error.StripeError as e:
        print(f"Ошибка при создании цены Stripe: {e}")
        raise


def create_stripe_checkout_session(price_id: str, payment_id: int):
    """
        Создает сессию Stripe Checkout для получения ссылки на оплату.
            Аргументы:
                price_id (str): ID цены Stripe (созданный ранее через create_stripe_price).
                payment_id (int): ID платежа из вашей локальной базы данных.
                                  Используется в метаданных для связывания сессии Stripe
                                  с вашим платежом при обратных вызовах.
            Возвращает:
                stripe.checkout.Session: Объект сессии Stripe Checkout, содержащий URL для оплаты.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при взаимодействии со Stripe API.
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
        Используется для проверки статуса платежа после перенаправления
        или при обработке веб-перехватчиками.
            Аргументы:
                session_id (str): ID сессии Stripe.
            Возвращает:
                stripe.checkout.Session: Объект сессии Stripe Checkout.
            Исключения:
                stripe.error.StripeError: Если произошла ошибка при взаимодействии со Stripe API
                                  (например, сессия не найдена или неверный ID).
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session
    except stripe.error.StripeError as e:
        print(f"Ошибка при получении сессии Stripe: {e}")
        raise


def process_payment_and_create_stripe_session(user, paid_course_id, paid_lesson_id):
    """
        Обрабатывает запрос на оплату, создает запись Payment в локальной системе
        и генерирует сессию Stripe для платных материалов.
        Если материал бесплатный или уже оплачен, возвращает соответствующее сообщение
        без создания новой сессии Stripe.
            Аргументы:
                user (User): Пользователь, совершающий оплату.
                paid_course_id (int): ID курса для оплаты (может быть None).
                paid_lesson_id (int): ID урока для оплаты (может быть None).
            Возвращает:
                dict: Словарь с информацией о платеже и ссылкой на оплату (payment_id, payment_url, amount, status, message).
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
    item_type = ""

    # Определение типа и стоимости оплачиваемого материала
    if paid_course_id:
        # Получаем курс. get_object_or_404 удобно для обработки несуществующих объектов
        course = get_object_or_404(Course, pk=paid_course_id)
        item_title = course.title
        item_type = "курс"
        amount_to_pay = course.actual_price  # Используем актуальную цену курса
        # Генерируем уникальный lookup_key для цены в Stripe
        price_lookup_key = f"course_{paid_course_id}_price_{int(amount_to_pay * 100)}"
    elif paid_lesson_id:
        # Получаем урок
        lesson = get_object_or_404(Lesson, pk=paid_lesson_id)
        item_title = lesson.title
        item_type = "урок"
        amount_to_pay = lesson.price  # Используем цену урока
        # Генерируем уникальный lookup_key для цены в Stripe
        price_lookup_key = f"lesson_{paid_lesson_id}_price_{int(amount_to_pay * 100)}"

    # Проверка на существующие успешные платежи за данный материал
    existing_succeeded_payment = Payment.objects.filter(
        user=user,
        status="succeeded",
        paid_course_id=paid_course_id,
        paid_lesson_id=paid_lesson_id,
    ).first()

    # Логика обработки бесплатных материалов и уже оплаченных
    if existing_succeeded_payment:
        if amount_to_pay > 0:
            # Если материал был получен бесплатно, но теперь он платный.
            # Продолжаем процесс оплаты, позволяя пользователю оплатить его.
            if existing_succeeded_payment.payment_method == "free":
                pass
            else:
                # Материал был оплачен ранее платным способом. Повторная покупка не требуется.
                return {
                    "payment_id": existing_succeeded_payment.id,
                    "payment_url": None,
                    "amount": existing_succeeded_payment.amount,
                    "status": existing_succeeded_payment.status,
                    "message": f"Вы уже приобрели этот {item_type} '{item_title}'. Повторная покупка не требуется.",
                }
        else:  # Если материал остался бесплатным (amount_to_pay <= 0)
            # Материал уже был получен (бесплатно или платно). Нет необходимости в повторной "покупке".
            return {
                "payment_id": existing_succeeded_payment.id,
                "payment_url": None,  # Нет URL для оплаты
                "amount": existing_succeeded_payment.amount,
                "status": existing_succeeded_payment.status,
                "message": f"Вы уже приобрели этот {item_type} '{item_title}'. Оплата не требуется.",
            }

    # Если existing_succeeded_payment отсутствует, или если он был 'free' для теперь платного материала:
    if amount_to_pay <= 0:
        # Создаём запись платежа как бесплатное "приобретение"
        payment = Payment.objects.create(
            user=user,
            paid_course_id=paid_course_id,
            paid_lesson_id=paid_lesson_id,
            amount=amount_to_pay,
            payment_method="free",
            status="succeeded",  # Сразу успешный статус
        )
        return {
            "payment_id": payment.id,
            "payment_url": None,  # Нет URL для оплаты
            "amount": payment.amount,
            "status": payment.status,
            "message": f"Данный {item_type} '{item_title}' является бесплатным, оплата не требуется.",
        }

    # Если материал платный (amount_to_pay > 0) и не был успешно приобретен ранее (или был приобретен бесплатно, а теперь стал платным)
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

        # Создаем или получаем цену в Stripe (сумма в копейках)
        stripe_price = create_stripe_price(int(amount_to_pay * 100), stripe_product.id, price_lookup_key)

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
