from typing import List, Optional, Tuple
from models import Client, Courier, Order


class OrderService:
    """
    Сервис управления заказами.
    """

    def __init__(self):
        self._orders: dict[int, Order] = {}
        self._couriers: List[Courier] = []
        self._clients: List[Client] = []
        self._product_catalog: List[Tuple[str, float]] = []  # (название, цена)
        self._next_order_id = 1

    # --- Заказы ---

    def create_order(self, client: Client, address: str) -> Order:
        """Создаёт новый заказ."""
        order = Order(self._next_order_id, client, address)
        self._orders[self._next_order_id] = order
        self._next_order_id += 1
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        """Возвращает заказ по ID или None."""
        return self._orders.get(order_id)

    def get_all_orders(self) -> List[Order]:
        """Возвращает список всех заказов."""
        return list(self._orders.values())

    # --- Курьеры ---

    def register_courier(self, name: str, phone: str) -> Courier:
        """Регистрирует нового курьера."""
        courier = Courier(name, phone)
        self._couriers.append(courier)
        return courier

    def get_all_couriers(self) -> List[Courier]:
        """Возвращает список всех курьеров."""
        return self._couriers.copy()

    def get_available_couriers(self) -> List[Courier]:
        """Возвращает список свободных курьеров."""
        return [c for c in self._couriers if c.is_available]

    def get_courier_by_index(self, index: int) -> Optional[Courier]:
        """Возвращает курьера по индексу в списке (для UI)."""
        if 0 <= index < len(self._couriers):
            return self._couriers[index]
        return None

    # --- Клиенты ---

    def register_client(self, name: str, phone: str) -> Client:
        """Регистрирует нового клиента."""
        client = Client(name, phone)
        self._clients.append(client)
        return client

    def get_all_clients(self) -> List[Client]:
        """Возвращает список всех клиентов."""
        return self._clients.copy()

    def get_client_by_index(self, index: int) -> Optional[Client]:
        """Возвращает клиента по индексу в списке (для UI)."""
        if 0 <= index < len(self._clients):
            return self._clients[index]
        return None

    # --- Каталог товаров ---

    def add_product(self, name: str, price: float) -> None:
        """Добавляет товар в каталог."""
        self._product_catalog.append((name, price))

    def get_product_catalog(self) -> List[Tuple[str, float]]:
        """Возвращает каталог товаров: список (название, цена)."""
        return self._product_catalog.copy()

    def get_product_by_index(self, index: int) -> Optional[Tuple[str, float]]:
        """Возвращает товар по индексу в каталоге (для UI)."""
        if 0 <= index < len(self._product_catalog):
            return self._product_catalog[index]
        return None