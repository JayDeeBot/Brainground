from pylsl import resolve_streams

streams = resolve_streams()
print(f"Found {len(streams)} stream(s).")
for s in streams:
    print(f"Name: {s.name()}, Type: {s.type()}, Channel count: {s.channel_count()}, Source ID: {s.source_id()}")