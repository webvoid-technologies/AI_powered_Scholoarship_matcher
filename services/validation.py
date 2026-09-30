from typing import Any, Dict, List, Tuple


REQUIRED_PROFILE_FIELDS = [
    'full_name',
    'education_level',
    'degree_branch',
    'year_of_study',
    'cgpa',
    'college_name',
    'location',
    'skills',
    'interests',
    'career_goal'
]


def validate_profile(data: Dict[str, Any]) -> Tuple[bool, str]:
    if not data:
        return False, 'No profile data provided.'

    for field in REQUIRED_PROFILE_FIELDS:
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return False, f'{field.replace("_", " ").title()} is required.'
        if field in ('skills', 'interests') and not isinstance(value, list):
            return False, f'{field.title()} must be a list.'

    cgpa = data.get('cgpa')
    try:
        cgpa_val = float(str(cgpa).strip())
    except (ValueError, TypeError):
        return False, 'CGPA / Percentage must be a valid number.'

    if cgpa_val < 0 or cgpa_val > 100:
        return False, 'CGPA / Percentage must be between 0 and 100.'

    return True, ''


def normalize_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        elif key in ('skills', 'interests') and isinstance(value, str):
            value = [v.strip() for v in value.split(',') if v.strip()]
        normalized[key] = value
    return normalized


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value
