import time
import re
import os
import io
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import csv
import pyvisa
import fire

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
        self.rm = pyvisa.ResourceManager()
        # self.rm = pyvisa.ResourceManager("@sim")
        print(self.rm.list_resources())
        self.instrument = None

    def run(self, path=r"docs/skippy_csv_syntax.csv", **kwargs):
        # print(path, kwargs)

        # Get File extension of file path
        file_ext = os.path.splitext(path)[1]
        if file_ext == '.txt':
            # Convert text file to csv format
            # Call execute
            raise ValueError
        elif file_ext == '.csv':
            # Parse csv file and execute commands
            variables, commands = self._parse_csv(path)
            self._execute(variables, commands)
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

    def _execute(self, variables: dict, commands: List[SkippyCommand]):
        address = variables.get("Address", "")
        termination = variables.get("Termination", "\n")

        # Connect to instrument
        self.instrument = self.rm.open_resource(address)

        for i, cmd in enumerate(commands, start=1):

            # Automatically add termination if not already included
            # Not needed here as its included by pyvisa
            # if termination and not full_command.endswith(termination.strip()):
            #     full_command = full_command + termination.strip()

            if cmd.special_op == "Iterate":
                iter_var_name = cmd.special_op_arg[1:] # Excluding the prefixed $ sign
                iter_count = int(self.variables[iter_var_name])
            else:
                iter_count = 1

            for X in range(1,iter_count+1):
                self.variables["X"]=str(X)
                # Substitute variables in command text
                full_command = self._substitute_vars(cmd.command or "")
                
                print(f"[{i}] {cmd.operation} → {full_command!r}")
                subcmds = full_command.split(";")

                for subcmd in subcmds:
                    op = cmd.operation.lower()

                    if op == "auto":
                        # If ends with ?, then query. Else, write.
                        if subcmd.strip().endswith("?"):
                            op = "query"
                        else:
                            op = "write"

                    # Execute operation
                    if op == "write":
                        self.instrument.write(subcmd)
                    elif op == "query":
                        response = self.instrument.query(subcmd)
                        print(f"  Response: {response.strip()}")
                        # Handle "Update" special operation
                        if cmd.special_op.lower() == "update" and cmd.special_op_arg.startswith("$"):
                            var_name = cmd.special_op_arg[1:]
                            self.variables[var_name] = response.strip()
                    elif op == "delay":
                        self._handle_delay(cmd.command)
                    elif op == "comment":
                        print(f"  # {cmd.command}")
                    else:
                        print(f"⚠️ Unknown operation '{cmd.operation}' — skipping.")

    def _substitute_vars(self, text: str) -> str:
        """Replace $Variable names in a command string with actual values."""
        pattern = re.compile(r"\$(\w+)")
        return pattern.sub(lambda m: self.variables.get(m.group(1), m.group(0)), text)
    
    def _handle_delay(self, delay_str: str):
        """Supports delays like 1s or 500ms."""
        delay_str = (delay_str or "").strip().lower()
        if delay_str.endswith("ms"):
            time.sleep(float(delay_str[:-2]) / 1000.0)
        elif delay_str.endswith("s"):
            time.sleep(float(delay_str[:-1]))
        elif delay_str:
            time.sleep(float(delay_str))

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
