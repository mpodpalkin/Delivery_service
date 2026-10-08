"""
Модуль консольного интерфейса.
"""
from typing import List, Optional, Any
from models import Order, OrderStatus, OrderItem
from delivery import DeliveryMethod, StandardDelivery, ExpressDelivery, PickupDelivery
from services import OrderService


class ConsoleUI:
    """Консольный интерфейс службы доставки."""

    DELIVERY_METHODS = [
        ("Стандартная доставка (2-3 дня)", StandardDelivery),
        ("Экспресс-доставка (2-4 часа)", ExpressDelivery),
        ("Самовывоз (сегодня)", PickupDelivery),
    ]

    def __init__(self, service: OrderService):
        self._service = service

    # ========================================================================
    # Главный цикл
    # ========================================================================

    def run(self) -> None:
        """Главный цикл меню."""
        while True:
            self._show_menu()
            choice = self._get_int_input("Выберите пункт меню (1-6): ", 1, 6)

            if choice is None:
                continue

            handlers = {
                1: self._create_order_flow,
                2: self._view_orders,
                3: self._change_status_flow,
                4: self._view_order_info,
                5: self._view_couriers,
                6: self._exit,
            }

            print()
            handlers[choice]()
            print()

    @staticmethod
    def _show_menu() -> None:
        """Выводит главное меню."""
        print("\n" + "═" * 50)
        print("ГЛАВНОЕ МЕНЮ")
        print("═" * 50)
        print("1. Создать заказ")
        print("2. Показать список заказов")
        print("3. Изменить статус заказа")
        print("4. Просмотреть информацию по заказу")
        print("5. Показать курьеров")
        print("6. Завершить работу")
        print("═" * 50)

    # ========================================================================
    # Пункт 1: Создание заказа (полный поток)
    # ========================================================================

    def _create_order_flow(self) -> None:
        """Полный поток создания заказа: клиент → адрес → товары → доставка → курьер."""
        print("═" * 50)
        print("СОЗДАНИЕ НОВОГО ЗАКАЗА")
        print("═" * 50)

        # --- Шаг 1: Выбор клиента ---
        clients = self._service.get_all_clients()
        if not clients:
            print("❌ Нет зарегистрированных клиентов")
            return

        print("\nШаг 1/5. Выберите клиента:")
        client = self._select_from_list(clients, "Клиент")
        if client is None:
            return

        # --- Шаг 2: Ввод адреса ---
        print("\nШаг 2/5. Ввод адреса")
        address = input("Введите адрес доставки: ").strip()
        if not address:
            print("❌ Адрес не может быть пустым")
            return

        # Создаём заказ
        order = self._service.create_order(client, address)
        print(f"\n✅ Заказ #{order.order_id} создан")

        # --- Шаг 3: Добавление товаров ---
        print("\nШаг 3/5. Добавление товаров")
        self._add_items_to_order(order)

        if not order.items:
            print("⚠️ Заказ создан без товаров. Вы можете добавить их позже.")

        # --- Шаг 4: Выбор способа доставки ---
        print("\nШаг 4/5. Выбор способа доставки")
        delivery_method = self._select_delivery_method()
        if delivery_method is None:
            print("⚠️ Способ доставки не выбран. Вы можете выбрать его позже.")
        else:
            order.set_delivery_method(delivery_method)
            print(f"\n✅ Способ доставки: {delivery_method}")
            print(f"   Стоимость доставки: {order.get_total_cost() - order.get_base_cost():.2f} руб.")
            print(f"   Срок: {delivery_method.get_estimated_time(order.created_at)}")

            # --- Шаг 5: Назначение курьера (если требуется) ---
            if delivery_method.requires_courier():
                print("\nШаг 5/5. Назначение курьера")
                self._assign_courier_to_order(order)
            else:
                print("\n✅ Курьер не требуется (самовывоз)")

        # --- Итог ---
        print("\n" + "─" * 50)
        print("ЗАКАЗ СОЗДАН:")
        print(order.get_info())

    def _add_items_to_order(self, order: Order) -> None:
        """Цикл добавления позиций в заказ."""
        catalog = self._service.get_product_catalog()
        if not catalog:
            print("⚠️ Каталог товаров пуст")
            return

        while True:
            print("\nТовары в каталоге:")
            for i, (name, price) in enumerate(catalog, 1):
                print(f"  {i}. {name} — {price:.2f} руб.")
            print("  0. Завершить добавление")

            choice = self._get_int_input("Выберите товар: ", 0, len(catalog))
            if choice is None or choice == 0:
                break

            product = self._service.get_product_by_index(choice - 1)
            if product is None:
                print("❌ Некорректный выбор")
                continue

            name, price = product
            quantity = self._get_int_input(f"Количество '{name}': ", 1, 999)
            if quantity is None:
                continue

            item = OrderItem(name, quantity, price)
            try:
                order.add_item(item)
                print(f"✅ Добавлено: {item}")
            except ValueError as e:
                print(f"❌ Ошибка: {e}")

    def _select_delivery_method(self) -> Optional[DeliveryMethod]:
        """Выбор способа доставки."""
        print("\nДоступные способы доставки:")
        for i, (name, _) in enumerate(self.DELIVERY_METHODS, 1):
            print(f"  {i}. {name}")
        print("  0. Пропустить (выбрать позже)")

        choice = self._get_int_input("Выберите способ доставки: ", 0, len(self.DELIVERY_METHODS))
        if choice is None or choice == 0:
            return None

        _, delivery_class = self.DELIVERY_METHODS[choice - 1]
        return delivery_class()

    def _assign_courier_to_order(self, order: Order) -> None:
        """Назначение курьера на заказ."""
        all_couriers = self._service.get_all_couriers()
        if not all_couriers:
            print("❌ Нет зарегистрированных курьеров")
            return

        print("\nСписок курьеров:")
        for i, courier in enumerate(all_couriers, 1):
            status = "🟢 свободен" if courier.is_available else "🔴 занят"
            print(f"  {i}. {courier.name} (тел: {courier.phone}) — {status}")

        available = self._service.get_available_couriers()

        if not available:
            print("\n⚠️ Все курьеры заняты")
            print("💡 Курьеры освобождаются после доставки или отмены заказа")
            choice = self._get_int_input(
                "Назначить курьера позже? (0 - да, пропустить): ", 0, 0
            )
            if choice is None or choice == 0:
                print("⚠️ Заказ создан без курьера. Назначьте его позже через меню.")
                return
        else:
            print(f"\nСвободных курьеров: {len(available)}")
            print("  0. Пропустить назначение курьера")
            choice = self._get_int_input(
                "Выберите курьера (номер из списка выше): ", 0, len(all_couriers)
            )
            if choice is None or choice == 0:
                print("⚠️ Курьер не назначен. Вы можете назначить его позже.")
                return

        courier = all_couriers[choice - 1]

        try:
            order.assign_courier(courier)
            print(f"✅ Курьер {courier.name} назначен")
        except ValueError as e:
            print(f"❌ Ошибка: {e}")

    # ========================================================================
    # Пункт 2: Список заказов
    # ========================================================================

    def _view_orders(self) -> None:
        """Показывает список всех заказов."""
        print("═" * 50)
        print("СПИСОК ЗАКАЗОВ")
        print("═" * 50)

        orders = self._service.get_all_orders()
        if not orders:
            print("Заказов пока нет")
            return

        for order in orders:
            print(f"\n{order}")

    # ========================================================================
    # Пункт 3: Изменение статуса
    # ========================================================================

    def _change_status_flow(self) -> None:
        """Изменение статуса заказа."""
        print("═" * 50)
        print("ИЗМЕНЕНИЕ СТАТУСА ЗАКАЗА")
        print("═" * 50)

        order = self._select_order()
        if order is None:
            return

        print(f"\nЗаказ #{order.order_id}")
        print(f"Текущий статус: {order.status.value}")

        valid_transitions = order.get_available_transitions()

        if not valid_transitions:
            print("❌ Из этого статуса нельзя перейти никуда")
            return

        print("\nДоступные переходы:")
        for i, status in enumerate(valid_transitions, 1):
            print(f"  {i}. {status.value}")
        print("  0. Отмена")

        choice = self._get_int_input("Выберите новый статус: ", 0, len(valid_transitions))
        if choice is None or choice == 0:
            return

        new_status = valid_transitions[choice - 1]

        try:
            order.change_status(new_status)
            print(f"\n✅ Статус изменён на: {new_status.value}")

            # Если курьер освобождён — сообщаем
            if new_status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
                print("🟢 Курьер освобождён")
        except ValueError as e:
            print(f"❌ Ошибка: {e}")

    # ========================================================================
    # Пункт 4: Информация по заказу
    # ========================================================================

    def _view_order_info(self) -> None:
        """Просмотр полной информации по заказу."""
        print("═" * 50)
        print("ИНФОРМАЦИЯ ПО ЗАКАЗУ")
        print("═" * 50)

        order = self._select_order()
        if order is None:
            return

        print("\n" + order.get_info())

    # ========================================================================
    # Пункт 5: Список курьеров
    # ========================================================================

    def _view_couriers(self) -> None:
        """Показывает всех курьеров и их статусы."""
        print("═" * 50)
        print("КУРЬЕРЫ")
        print("═" * 50)

        couriers = self._service.get_all_couriers()
        if not couriers:
            print("Нет зарегистрированных курьеров")
            return

        for i, courier in enumerate(couriers, 1):
            status = "🟢 свободен" if courier.is_available else "🔴 занят"
            print(f"  {i}. {courier.name} (тел: {courier.phone}) — {status}")

        # Статистика
        available = len(self._service.get_available_couriers())
        total = len(couriers)
        print(f"\nВсего: {total} | Свободных: {available} | Занятых: {total - available}")

    # ========================================================================
    # Пункт 6: Выход
    # ========================================================================

    @staticmethod
    def _exit() -> None:
        """Завершает работу программы."""
        print("\nДо свидания!")
        exit(0)

    # ========================================================================
    # Вспомогательные методы
    # ========================================================================

    def _select_order(self) -> Optional[Order]:
        """Выбор заказа из списка."""
        orders = self._service.get_all_orders()
        if not orders:
            print("❌ Нет заказов")
            return None

        print("\nСписок заказов:")
        for order in orders:
            print(f"  {order}")

        order_id = self._get_int_input("\nВведите номер заказа (0 для отмены): ", 0, 9999)
        if order_id is None or order_id == 0:
            return None

        order = self._service.get_order(order_id)
        if order is None:
            print(f"❌ Заказ #{order_id} не найден")
            return None

        return order

    def _select_from_list(self, items: List[Any], item_name: str) -> Optional[Any]:
        """Выбор элемента из списка."""
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        print("  0. Отмена")

        choice = self._get_int_input(f"Выберите {item_name.lower()}а: ", 0, len(items))
        if choice is None or choice == 0:
            return None

        return items[choice - 1]

    @staticmethod
    def _get_int_input(prompt: str, min_val: int, max_val: int) -> Optional[int]:
        """Безопасный ввод целого числа с проверкой диапазона."""
        while True:
            try:
                value = int(input(prompt))
                if min_val <= value <= max_val:
                    return value
                print(f"❌ Введите число от {min_val} до {max_val}")
            except ValueError:
                print("❌ Введите целое число")