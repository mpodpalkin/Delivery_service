from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class DeliveryMethod(ABC):
    WORK_START_HOUR = 8  # Начало рабочего дня
    WORK_END_HOUR = 22  # Конец рабочего дня

    @abstractmethod
    def calculate_cost(self, base_cost: float) -> float:
        """
        Рассчитывает итоговую стоимость с учётом доставки.
        :param base_cost: стоимость товаров в заказе
        :return: итоговая стоимость
        """
        ...

    @abstractmethod
    def get_estimated_time(self, order_time: datetime) -> str:
        """Возвращает ориентировочный срок доставки."""
        ...

    @abstractmethod
    def requires_courier(self) -> bool:
        """Требует ли этот способ назначения курьера."""
        ...

    def __str__(self) -> str:
        """Название способа доставки для вывода в UI."""
        return self.__class__.__name__


class StandardDelivery(DeliveryMethod):
    """
    Стандартная доставка: 2-3 дня.
    """
    DELIVERY_FEE = 300.0

    def calculate_cost(self, base_cost: float) -> float:
        return base_cost + self.DELIVERY_FEE

    def get_estimated_time(self, order_time: datetime) -> str:
        # Доставка через 2-3 дня
        start_date = order_time + timedelta(days=2)
        end_date = order_time + timedelta(days=3)

        # Временное окно доставки: общие рабочие часы
        start = start_date.replace(hour=self.WORK_START_HOUR, minute=0, second=0, microsecond=0)
        end = end_date.replace(hour=self.WORK_END_HOUR, minute=0, second=0, microsecond=0)

        return f"{start.strftime('%d.%m')} с {self.WORK_START_HOUR:02d}:00 до {end.strftime('%d.%m')} {self.WORK_END_HOUR:02d}:00"

    def requires_courier(self) -> bool:
        return True


class ExpressDelivery(DeliveryMethod):
    """
    Экспресс-доставка: 2-4 часа от момента заказа.
    Работает только в рабочие часы службы (08:00-22:00).
    """
    DELIVERY_FEE = 800.0

    def calculate_cost(self, base_cost: float) -> float:
        return base_cost + self.DELIVERY_FEE

    def get_estimated_time(self, order_time: datetime) -> str:
        # ПРАВИЛО 1: Если заказ создан поздно вечером (после 20:00),
        # экспресс-доставка "сегодня" уже невозможна
        if order_time.hour >= 20:
            tomorrow = order_time + timedelta(days=1)
            start = tomorrow.replace(hour=self.WORK_START_HOUR, minute=0, second=0, microsecond=0)
            end = tomorrow.replace(hour=self.WORK_START_HOUR + 2, minute=0, second=0, microsecond=0)
            return f"завтра с {start.strftime('%H:%M')} до {end.strftime('%H:%M')}"

        # Рассчитываем базовый интервал +2-4 часа
        start = order_time + timedelta(hours=2)
        end = order_time + timedelta(hours=4)

        # ПРАВИЛО 2: Если расчётное время выходит за рабочие часы
        if end.hour >= self.WORK_END_HOUR or start.hour < self.WORK_START_HOUR:
            tomorrow = order_time + timedelta(days=1)
            start = tomorrow.replace(hour=self.WORK_START_HOUR, minute=0, second=0, microsecond=0)
            end = tomorrow.replace(hour=self.WORK_START_HOUR + 2, minute=0, second=0, microsecond=0)
            return f"завтра с {start.strftime('%H:%M')} до {end.strftime('%H:%M')}"

        # Обычный случай: всё в рабочих часах
        if start.date() == datetime.now().date():
            return f"сегодня с {start.strftime('%H:%M')} до {end.strftime('%H:%M')}"
        else:
            return f"{start.strftime('%d.%m')} {start.strftime('%H:%M')} — {end.strftime('%H:%M')}"

    def requires_courier(self) -> bool:
        return True


class PickupDelivery(DeliveryMethod):
    """
    Самовывоз из пункта выдачи.
    """

    def calculate_cost(self, base_cost: float) -> float:
        return base_cost

    def get_estimated_time(self, order_time: datetime) -> str:
        # ПРАВИЛО: Если заказ создан после закрытия — переносим на завтра
        if order_time.hour >= self.WORK_END_HOUR:
            tomorrow = order_time + timedelta(days=1)
            pickup_start = tomorrow.replace(hour=self.WORK_START_HOUR, minute=0, second=0, microsecond=0)
            pickup_end = tomorrow.replace(hour=self.WORK_END_HOUR, minute=0, second=0, microsecond=0)
            return f"завтра с {pickup_start.strftime('%H:%M')} до {pickup_end.strftime('%H:%M')}"

        # Обычный случай: можно забрать сегодня в рабочие часы
        pickup_start = order_time.replace(hour=self.WORK_START_HOUR, minute=0, second=0, microsecond=0)
        pickup_end = order_time.replace(hour=self.WORK_END_HOUR, minute=0, second=0, microsecond=0)
        return f"сегодня с {pickup_start.strftime('%H:%M')} до {pickup_end.strftime('%H:%M')}"

    def requires_courier(self) -> bool:
        return False