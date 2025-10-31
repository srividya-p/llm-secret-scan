from enum import Enum


class FindingType(Enum):
    SECRET_LEAK = "SECRET_LEAK"
    INFORMATION_DISCLOSURE = "INFORMATION_DISCLOSURE"
    NO_LEAK = "NO_LEAK"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, type_str: str) -> "FindingType":
        if not type_str:
            return cls.UNKNOWN

        type_str = type_str.lower()

        if any(
            keyword in type_str
            for keyword in ["secret", "credential", "password", "key", "token", "api"]
        ):
            return cls.SECRET_LEAK
        elif any(
            keyword in type_str
            for keyword in ["info", "information", "config", "disclosure"]
        ):
            return cls.INFORMATION_DISCLOSURE
        elif any(keyword in type_str for keyword in ["no", "none", "safe", "clean"]):
            return cls.NO_LEAK
        return cls.UNKNOWN

    def to_dict(self) -> str:
        return self.value
