def add_numbers(
    a: int,
    b: int,
    *numbers: int,
    initial: int = 0,
) -> int:
    """두 개 이상의 정수의 합에 시작값 initial을 더해 반환합니다."""
    # initial을 생략하면 기존처럼 전달받은 숫자만 합산합니다.
    return a + b + sum(numbers) + initial


def subtract_numbers(a: int, b: int) -> int:
    """첫 번째 정수에서 두 번째 정수를 뺍니다. 예: subtract_numbers(8, 3)은 5입니다."""
    return a - b


def multiply_numbers(a: int, b: int, c: int = 1) -> int:
    """두 정수 또는 세 정수의 곱을 반환합니다."""
    # 세 번째 숫자를 생략하면 기존 두 정수의 곱과 같습니다.
    return a * b * c


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
    """문자열의 양끝 공백을 제거한 뒤 영문자를 대문자로 바꿉니다."""
    return text.strip().upper()


def count_items(items: list[int]) -> int:
    """리스트의 원소 개수를 반환합니다. 빈 리스트의 원소 개수는 0입니다."""
    return len(items)