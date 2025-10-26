import pyvisa
import fire
import os
import io
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import csv

@dataclass
class SkippyCommand:
    address: str                     # e.g., "$Address"
    operation: str                   # e.g., "Write", "Query", "Delay", "Comment"
    command: Optional[str] = ""      # SCPI command string, e.g., "*COUNT?"
    special_op: Optional[str] = ""   # e.g., "Update", "Iterate"
    special_op_arg: Optional[str] = ""  # e.g., "$Count"

class Skippy():
    def __init__(self):
        self.variables = {}
        self.commands = []

    def run(self, path=r"docs/skippy_csv_syntax.csv", **kwargs):
        # print(path, kwargs)

        # Get File extension of file path
        file_ext = os.path.splitext(path)[1]
        if file_ext == '.txt':
            # Convert text file to csv format
            # Call execute
            pass
        elif file_ext == '.csv':
            # Parse csv file
            self._parse_csv(path)
            print(self.variables)
            print(self.commands)
            # Call execute
            pass
        else:
            raise ValueError

    def _parse_csv(self, path) -> Tuple[Dict[str, str], List[SkippyCommand]]:
            self.variables.clear()
            self.commands.clear()

            sections: List[str] = []
            current_section_lines: List[str] = []

            # Read the file line-by-line and split into two sections, one for each table
            with open(path, encoding="utf-8") as f:
                for line in f:
                    # Split on rows that are entirely empty or contain only commas/spaces
                    if not any(cell.strip() for cell in line.split(",")):
                        if current_section_lines:
                            # Save the current section as a string
                            sections.append("\n".join(current_section_lines).strip())
                            current_section_lines = []
                    else:
                        # Add non-empty line to current section
                        current_section_lines.append(line.rstrip())

                # Add the last section, if not empty
                if current_section_lines:
                    sections.append("\n".join(current_section_lines).strip())

            # --- Table 1: Variables ---
            var_rows = csv.DictReader(io.StringIO(sections[0]))
            for row in var_rows:
                key = row.get("Variable", "").strip()
                val = row.get("Value", "").strip()
                if key:
                    self.variables[key] = val

            # --- Table 2: Commands ---
            cmd_rows = csv.DictReader(io.StringIO(sections[1]))
            for row in cmd_rows:
                cmd = SkippyCommand(
                    address=row.get("Address", "").strip(),
                    operation=row.get("Operation", "").strip(),
                    command=row.get("Command", "").strip(),
                    special_op=row.get("SpecialOp", "").strip(),
                    special_op_arg=row.get("SpecialOpArg", "").strip()
                )
                self.commands.append(cmd)

            return self.variables, self.commands

def main():
    print("Hello from skippy!")
    skippy = Skippy()
    skippy.run(r"docs/skippy_csv_syntax.csv")
    # rm = pyvisa.ResourceManager()
    # # rm = pyvisa.ResourceManager('@sim')
    # print(rm.list_resources())
    # inst = rm.open_resource('ASRL1::INSTR', read_termination='\n')
    # print(inst.query("*IDN?"))


if __name__ == "__main__":
    # main()
    fire.Fire(Skippy)
