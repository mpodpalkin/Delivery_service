import re
from datetime import datetime
from enum import Enum
from typing import List, Optional

from delivery import DeliveryMethod


class OrderStatus(Enum):
    """Статусы заказа."""
    NEW = "Новый"
    PROCESSING = "В обработке"
    OUT_FOR_DELIVERY = "Передан курьеру"
    DELIVERED = "Доставлен"
    CANCELLED = "Отменен"

class User:
    """Базовый класс для людей (клиент и курьер)."""

    def __init__(self, name: str, phone: str):
        # Валидация имени
        if not name or not name.strip():
            raise ValueError("Имя не может быть пустым")

        # Валидация телефона
        self._phone = self._validate_phone(phone)
        self._name = name.strip()

    @staticmethod
    def _validate_phone(phone: str) -> str:
        """
        Проверяет, что телефон содержит ровно 10 цифр.
        Допускает ввод с пробелами, скобками, дефисами и '+' —
        они будут удалены перед проверкой.
        """
        if not phone:
            raise ValueError("Телефон не может быть пустым")

        # Убираем все символы кроме цифр
        digits_only = re.sub(r'\D', '', phone)

        if len(digits_only) != 10:
            raise ValueError(
                f"Телефон должен содержать ровно 10 цифр "
                f"(получено: {len(digits_only)} цифр из '{phone}')"
            )

        return digits_only

    @property
    def name(self) -> str:
        return self._name

    @property
    def phone(self) -> str:
        return self._phone

    def get_contact_info(self) -> str:
        """Возвращает строку с контактной информацией."""
        return f"{self._name} (тел: {self._phone})"

    def __str__(self) -> str:
        return self.get_contact_info()


class Client(User):
    """Клиент службы доставки."""

    def __init__(self, name: str, phone: str):
        super().__init__(name, phone)

    def __str__(self) -> str:
        return f"{super().__str__()}"


class Courier(User):
    """Курьер службы доставки."""

    def __init__(self, name: str, phone: str):
        super().__init__(name, phone)
        self._is_available = True  # Инкапсулированное состояние

    @property
    def is_available(self) -> bool:
        return self._is_available

    def mark_busy(self) -> None:
        """Пометить курьера как занятого."""
        if not self._is_available:
            raise ValueError(f"Курьер {self._name} уже занят")
        self._is_available = False

    def mark_free(self) -> None:
        """Освободить курьера."""
        self._is_available = True

    def __str__(self) -> str:
        status = "свободен" if self._is_available else "занят"
        return f"{super().__str__()} [{status}]"


class OrderItem:
    """Позиция заказа: товар, количество, цена."""

    def __init__(self, product_name: str, quantity: int, price: float):
        if not product_name or not product_name.strip():
            raise ValueError("Название товара не может быть пустым")
        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля")
        if price < 0:
            raise ValueError("Цена не может быть отрицательной")

        self._product_name = product_name.strip()
        self._quantity = quantity
        self._price = price

    @property
    def product_name(self) -> str:
        return self._product_name

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def price(self) -> float:
        return self._price

    def get_total_cost(self) -> float:
        """Стоимость позиции = количество * цена."""
        return self._quantity * self._price

    def __str__(self) -> str:
        return f"{self._product_name} x{self._quantity} = {self.get_total_cost():.2f} руб."


class Order:
    """Заказ службы доставки."""
    _VALID_TRANSITIONS = {
        OrderStatus.NEW: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
        OrderStatus.PROCESSING: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
        OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
        OrderStatus.DELIVERED: [],
        OrderStatus.CANCELLED: [],
    }

    def __init__(self, order_id: int, client: Client, address: str):
        if order_id <= 0:
            raise ValueError("ID заказа должен быть положительным")
        if not address or not address.strip():
            raise ValueError("Адрес доставки не может быть пустым")

        # Инкапсулированные поля (внутреннее состояние)
        self._order_id = order_id
        self._client = client
        self._address = address.strip()
        self._items: List[OrderItem] = []  # Композиция: заказ владеет позициями
        self._delivery_method = None  # Ссылка на стратегию доставки
        self._courier: Optional[Courier] = None
        self._status = OrderStatus.NEW
        self._created_at = datetime.now()

    # Геттеры (только чтение)
    @property
    def order_id(self) -> int:
        return self._order_id

    @property
    def client(self) -> Client:
        return self._client

    @property
    def address(self) -> str:
        return self._address

    @property
    def items(self) -> List[OrderItem]:
        return self._items.copy()  # Возвращаем копию для защиты

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def delivery_method(self):
        return self._delivery_method

    @property
    def courier(self) -> Optional[Courier]:
        return self._courier

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # --- Методы изменения состояния с проверками ---
    def add_item(self, item: OrderItem) -> None:
        """Добавить позицию в заказ."""
        if self._status != OrderStatus.NEW:
            raise ValueError("Нельзя добавлять товары в заказ, который уже в обработке")
        self._items.append(item)

    def set_delivery_method(self, method: DeliveryMethod) -> None:
        """Установить способ доставки."""
        if not self._items:
            raise ValueError("Нельзя выбрать доставку для пустого заказа — добавьте хотя бы одну позицию")

        if self._status not in (OrderStatus.NEW, OrderStatus.PROCESSING):
            raise ValueError("Нельзя изменить способ доставки для текущего статуса")

        # Если был назначен курьер, а новый метод не требует курьера — освобождаем
        if self._courier and not method.requires_courier():
            self._courier.mark_free()
            self._courier = None

        self._delivery_method = method

    def assign_courier(self, courier: Courier) -> None:
        """Назначить курьера на заказ."""
        if self._delivery_method is None:
            raise ValueError("Сначала выберите способ доставки")

        if not self._delivery_method.requires_courier():
            raise ValueError(f"Способ доставки '{self._delivery_method.__class__.__name__}' не требует курьера")

        if not courier.is_available:
            raise ValueError(f"Курьер {courier.name} уже занят")

        # Освобождаем предыдущего курьера, если был
        if self._courier:
            self._courier.mark_free()

        courier.mark_busy()
        self._courier = courier

    def change_status(self, new_status: OrderStatus) -> None:
        """Изменить статус заказа с проверкой допустимости перехода."""
        if not isinstance(new_status, OrderStatus):
            raise ValueError("Некорректный статус")

        allowed = self._VALID_TRANSITIONS.get(self._status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Недопустимый переход: {self._status.value} → {new_status.value}"
            )

        # Освобождаем курьера при завершении или отмене
        if new_status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            if self._courier:
                self._courier.mark_free()
                self._courier = None

        self._status = new_status

    def get_base_cost(self) -> float:
        """Стоимость товаров без учёта доставки."""
        return sum(item.get_total_cost() for item in self._items)

    def get_total_cost(self) -> float:
        """Итоговая стоимость с учётом доставки."""
        base = self.get_base_cost()
        if self._delivery_method:
            return self._delivery_method.calculate_cost(base)
        return base

    def get_info(self) -> str:
        """Полная информация о заказе."""
        lines = [
            f"═══ Заказ #{self._order_id} ═══",
            f"Создан: {self._created_at.strftime('%d.%m.%Y %H:%M')}",
            f"Статус: {self._status.value}",
            f"Клиент: {self._client}",
            f"Адрес: {self._address}",
            "Позиции:",
        ]

        if self._items:
            for item in self._items:
                lines.append(f"  • {item}")

        lines.append(f"Стоимость товаров: {self.get_base_cost():.2f} руб.")

        if self._delivery_method:
            lines.append(f"Доставка: {self._delivery_method.__class__.__name__}")
            lines.append(f"  Стоимость доставки: {self.get_total_cost() - self.get_base_cost():.2f} руб.")
            lines.append(f"  Срок: {self._delivery_method.get_estimated_time(self._created_at)}")
        else:
            lines.append("Доставка: не выбрана")

        if self._courier:
            lines.append(f"Курьер: {self._courier}")
        elif self._delivery_method and self._delivery_method.requires_courier():
            lines.append("Курьер: не назначен")

        lines.append(f"ИТОГО: {self.get_total_cost():.2f} руб.")
        return "\n".join(lines)

    def get_available_transitions(self) -> List[OrderStatus]:
        return self._VALID_TRANSITIONS.get(self._status, [])

    def __str__(self) -> str:
        return f"Заказ #{self._order_id} [{self._status.value}]"