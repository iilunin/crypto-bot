import os


def get_symbol_and_id_from_file_path(file_path):
    file_name, _ = os.path.splitext(os.path.basename(file_path))
    parts = file_name.split('_')
    return parts[0], parts[1] if len(parts) > 1 else None

def get_file_name(symbol, id):
    return '{}_{}.json'.format(symbol, id)


def s2b(s):
    if isinstance(s, bool):
        return s
    if s is None:
        return None
    if s.lower() in ['true', 'yes', '1']:
        return True
    return False

def is_simulation():
    return s2b(os.environ.get("SIMULTATE", False))
