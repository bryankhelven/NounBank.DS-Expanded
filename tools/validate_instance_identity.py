"""Validate the universal public predicate identity contract before publication."""
from pathlib import Path
import json
import sys
import zipfile


def validate(root):
    root = Path(root)
    entries = json.loads((root / 'jsons/_manifest.json').read_text())['lemmas']
    identifiers = set()
    instances = 0
    documents = []
    for entry in entries:
        path = root / 'jsons' / entry['filename']
        document = json.loads(path.read_text())
        documents.append(document)
        for sense in document['senses']:
            for example in sense['examples']:
                identifier = example.get('instance_id')
                assert isinstance(identifier, str) and identifier, f'{path}: missing instance_id'
                assert identifier not in identifiers, f'{path}: repeated instance_id {identifier}'
                identifiers.add(identifier)
                predicate = example.get('predicate', {})
                for field in ('form', 'char_start', 'char_end', 'occurrence_index', 'occurrence_count', 'char_offset_unit'):
                    assert field in predicate, f'{identifier}: missing predicate.{field}'
                start, end = predicate['char_start'], predicate['char_end']
                assert type(start) is int and type(end) is int, f'{identifier}: noninteger limits'
                assert 0 <= start < end <= len(example['text']), f'{identifier}: invalid limits'
                assert example['text'][start:end] == predicate['form'], f'{identifier}: wrong literal anchor'
                index, count = predicate['occurrence_index'], predicate['occurrence_count']
                assert type(index) is int and type(count) is int and 1 <= index <= count, f'{identifier}: invalid occurrence ordinal'
                assert predicate['char_offset_unit'] == 'UNICODE_CODEPOINT_END_EXCLUSIVE', f'{identifier}: wrong offset convention'
                for annotation in example.get('argm_annotations', []):
                    assert annotation['native_instance_id'] == identifier, f'{identifier}: broken ARG-M identity link'
                instances += 1
    aggregate = [json.loads(line) for line in (root / 'jsons/nounbank.ds_expanded_all.jsonl').read_text().splitlines()]
    assert aggregate == documents, 'JSONL differs from the individual JSONs'
    with zipfile.ZipFile(root / 'jsons/nounbank.ds_expanded_all_jsons.zip') as archive:
        assert archive.testzip() is None, 'Damaged aggregate ZIP'
        for entry, document in zip(entries, documents):
            assert json.loads(archive.read(entry['filename'])) == document, f"ZIP differs: {entry['filename']}"
    return {'lemmas': len(entries), 'instances': instances}


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    print('INSTANCE IDENTITY PASS:', validate(root))
