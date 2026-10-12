from services import OrderService

# Тестовые справочники

# Каталог товаров (название, цена за штуку)
PRODUCT_CATALOG = [
    ("Пицца Маргарита", 450.0),
    ("Пицца Пепперони", 550.0),
    ("Кола 0.5л", 120.0),
    ("Суши-сет Филадельфия", 1200.0),
    ("Мисо-суп", 250.0),
    ("Бургер Классик", 350.0),
    ("Картофель фри", 180.0),
    ("Чай зелёный", 90.0),
]

# База клиентов (имя, телефон)
TEST_CLIENTS = [
    ("Иван Петров", "9991234567"),
    ("Анна Смирнова", "9999876543"),
    ("Олег Козлов", "9995556677"),
    ("Елена Волкова", "9991112288"),
]

# База курьеров (имя, телефон)
TEST_COURIERS = [
    ("Алексей Иванов", "9993334455"),
    ("Мария Петрова", "9994445566"),
    ("Дмитрий Сидоров", "9997778899"),
]

# Инициализация
def init_service(service: OrderService) -> None:
    """Заполняет сервис тестовыми справочниками."""

    # Регистрируем курьеров
    for name, phone in TEST_COURIERS:
        service.register_courier(name, phone)

    # Регистрируем клиентов
    for name, phone in TEST_CLIENTS:
        service.register_client(name, phone)

    # Заполняем каталог товаров
    for name, price in PRODUCT_CATALOG:
        service.add_product(name, price)

    print(f" Загружено:")
    print(f"   • Курьеров: {len(TEST_COURIERS)}")
    print(f"   • Клиентов: {len(TEST_CLIENTS)}")
    print(f"   • Товаров в каталоге: {len(PRODUCT_CATALOG)}")


def main() -> None:
    """Инициализация справочников и запуск интерфейса."""
    print("═" * 50)
    print("   СЛУЖБА ДОСТАВКИ — Консольный симулятор")
    print("═" * 50)
    print()

    # 1. Создаём сервис
    service = OrderService()

    # 2. Заполняем справочники (но не создаём заказов)
    init_service(service)
    print()

    # 3. Запускаем консольный интерфейс
    from ui import ConsoleUI
    ui = ConsoleUI(service)
    ui.run()


if __name__ == "__main__":
    main()