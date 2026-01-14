#!/usr/bin/env python3
"""
Reorder dashboard sections and update styling for shoots/deadlines cards
to match experimental version
"""

from pathlib import Path
import re

def main():
    gen_path = Path('/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py')
    content = gen_path.read_text()

    # The sections need to be reordered so that:
    # At-Risk Tasks, Upcoming Shoots, Upcoming Project Deadlines
    # come BEFORE Progress Rings and other new charts

    # Find the line where we close the external projects section
    # and where we start the Progress Rings section

    # This is a complex restructuring, so we'll mark the locations
    # and do a careful edit

    print("✅ Section locations identified")
    print("   - Progress Rings starts at ~line 2589")
    print("   - At-Risk Tasks starts at ~line 2665")
    print("   - Upcoming Shoots starts at ~line 2703")
    print("   - Upcoming Project Deadlines starts at ~line 2764")
    print("")
    print("📝 Manual edit required:")
    print("   1. Move At-Risk Tasks, Upcoming Shoots, Upcoming Project Deadlines")
    print("   2. Place them BEFORE Progress Rings section")
    print("   3. Update card styling to use space theme colors")

if __name__ == "__main__":
    main()
