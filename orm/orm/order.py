import enum


class OrderType(enum.Enum):
    ASC = 0
    DESC = 1


class Order:
    @staticmethod
    def ASC(field: str) -> tuple[OrderType, str]:
        return (OrderType.ASC, field)

    @staticmethod
    def DESC(field: str) -> tuple[OrderType, str]:
        return (OrderType.DESC, field)
