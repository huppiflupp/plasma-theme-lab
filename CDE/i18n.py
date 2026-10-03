"""Compile the theme's gettext catalogs, with no Python dependencies."""
import ast
from pathlib import Path
import shutil
import struct
import subprocess


def _read_po(path):
    """Read UTF-8 PO entries, including contexts and plural translations."""
    messages = {}
    entry = {}
    field = None
    fuzzy = False

    def finish():
        if 'msgid' not in entry or fuzzy:
            return
        key = entry['msgid']
        if 'msgctxt' in entry:
            key = entry['msgctxt'] + '\x04' + key
        if 'msgid_plural' in entry:
            key += '\x00' + entry['msgid_plural']
            indices = sorted(int(k[7:-1]) for k in entry if k.startswith('msgstr['))
            if indices != list(range(len(indices))):
                raise ValueError(f'{path}: non-contiguous plural translations')
            value = '\x00'.join(entry[f'msgstr[{i}]'] for i in indices)
        else:
            value = entry.get('msgstr', '')
        if value:
            messages[key] = value

    for number, raw in enumerate(Path(path).read_text(encoding='utf-8').splitlines() + [''], 1):
        line = raw.strip()
        if not line:
            finish()
            entry, field, fuzzy = {}, None, False
        elif line.startswith('#,'):
            fuzzy = fuzzy or 'fuzzy' in [flag.strip() for flag in line[2:].split(',')]
        elif line.startswith('#'):
            continue
        elif line.startswith('"'):
            if field is None:
                raise ValueError(f'{path}:{number}: orphan continuation')
            entry[field] += ast.literal_eval(line)
        else:
            field, literal = line.split(None, 1)
            if field not in ('msgctxt', 'msgid', 'msgid_plural', 'msgstr') and not (field.startswith('msgstr[') and field.endswith(']')):
                raise ValueError(f'{path}:{number}: unknown field {field}')
            entry[field] = ast.literal_eval(literal)
    return messages


def _compile_po(source, target):
    messages = _read_po(source)
    keys = sorted(messages, key=lambda key: key.encode('utf-8'))
    originals = [key.encode('utf-8') for key in keys]
    translations = [messages[key].encode('utf-8') for key in keys]
    count = len(keys)
    offset = 28 + 16 * count
    tables = []
    data = bytearray()
    for strings in (originals, translations):
        for string in strings:
            tables.append((len(string), offset + len(data)))
            data.extend(string + b'\x00')
    header = struct.pack('<7I', 0x950412de, 0, count, 28, 28 + 8 * count, 0, 0)
    target.write_bytes(header + b''.join(struct.pack('<2I', *item) for item in tables) + data)


def compile_translations(out_dir):
    """Compile every po/*.po into out_dir/locale/<language>/LC_MESSAGES/."""
    msgfmt = shutil.which('msgfmt')
    outputs = []
    for source in sorted((Path(__file__).resolve().parent / 'po').glob('*.po')):
        target = Path(out_dir) / 'locale' / source.stem / 'LC_MESSAGES' / 'cde-copper.mo'
        target.parent.mkdir(parents=True, exist_ok=True)
        if msgfmt:
            subprocess.run([msgfmt, '--check', '-o', str(target), str(source)], check=True)
        else:
            _compile_po(source, target)
        outputs.append(target)
    return outputs
