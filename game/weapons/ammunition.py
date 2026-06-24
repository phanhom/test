"""弹药系统"""


class Magazine:
    """弹匣"""

    def __init__(self, capacity: int, current: int = None):
        self.capacity = max(1, capacity)
        self.current = current if current is not None else self.capacity

    def is_empty(self) -> bool:
        return self.current <= 0

    def is_full(self) -> bool:
        return self.current >= self.capacity

    def shoot(self) -> bool:
        if self.is_empty():
            return False
        self.current -= 1
        return True

    def reload(self) -> bool:
        if self.is_full():
            return False
        self.current = self.capacity
        return True

    def add_ammo(self, amount: int) -> int:
        """添加弹药，返回实际添加量"""
        if amount <= 0:
            return 0
        old = self.current
        self.current = min(self.capacity, self.current + amount)
        return self.current - old

    def to_dict(self) -> dict:
        return {"capacity": self.capacity, "current": self.current}

    def from_dict(self, data: dict):
        self.capacity = data.get("capacity", self.capacity)
        self.current = data.get("current", self.current)
