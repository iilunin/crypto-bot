import os

from Bot import Trade


def get_symbol_and_id_from_file_path(file_path):
    file_name, _ = os.path.splitext(os.path.basename(file_path))
    parts = file_name.split('_')
    return parts[0], parts[1] if len(parts) > 1 else None

def get_file_name(trade: Trade):
    return '{}_{}.json'.format(trade.symbol, trade.id)
