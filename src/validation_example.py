def add_numbers(a: int, b: int) -> int:
    """두 정수의 합을 반환합니다. 예: add_numbers(5, 3)은 8입니다."""
    return a + b


def subtract_numbers(a: int, b: int) -> int:
    """첫 번째 정수에서 두 번째 정수를 뺍니다. 예: subtract_numbers(8, 3)은 5입니다."""
    return a - b


def multiply_numbers(a: int, b: int) -> int:
    """두 정수의 곱을 반환합니다. 예: multiply_numbers(4, 3)은 12입니다."""
    return a * b


def square(number: int) -> int:
    """정수의 제곱을 반환합니다. 예: square(3)은 9입니다."""
    return number ** 2


def is_even(number: int) -> bool:
    """짝수이면 True, 홀수이면 False를 반환합니다. 0은 짝수입니다."""
    return number % 2 == 0


def larger_number(a: int, b: int) -> int:
    """두 정수 중 더 큰 값을 반환합니다. 두 값이 같으면 그 값을 반환합니다."""
    return max(a, b)


def absolute_value(number: int) -> int:
    """정수의 절댓값을 반환합니다. 예: -5와 5의 절댓값은 모두 5입니다."""
    return abs(number)


def reverse_text(text: str) -> str:
    """문자열을 역순으로 반환합니다. 예: 'abc'는 'cba'가 됩니다."""
    return text[::-1]


def to_uppercase(text: str) -> str:
    """영문자를 대문자로 바꿉니다. 예: 'hello'는 'HELLO'가 됩니다."""
    return text.upper()


def count_items(items: list[int]) -> int:
    """리스트의 원소 개수를 반환합니다. 빈 리스트의 원소 개수는 0입니다."""
    return len(items)