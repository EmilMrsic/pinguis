import sys
print("💥 run_record.py starting up...")
from pinguis.recorder import record

port = sys.argv[1] if len(sys.argv) > 1 else None
record(output_file="output.edf", duration=5, port=port)
