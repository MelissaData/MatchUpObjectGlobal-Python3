"""
MatchUp Object Global is an extremely fast and powerful programmer's tool that can be
integrated into custom applications to eliminate duplicate records.

High-level flow of this sample:
  1. SETUP     - create an mdMUReadWrite instance, license it, point it at the data
                 files, choose a matchcode, then InitializeDataFiles() (one time).
  2. INPUT     - read a pipe-delimited input file record by record.
  3. PROCESS   - for each record map its fields, BuildKey() and WriteRecord(); then
                 Process() runs the dedupe pass across all records.
  4. READ      - ReadRecord() each processed record and read its result codes, dupe
                 group, and key; write them to an output file.
  5. INTERPRET - a result code of "MS03" marks a record as a duplicate.

The pieces in this file map onto that flow:
  - run_as_console / parse_arguments : console harness (argument parsing + the interactive loop).
  - MatchUpObjectGlobal              : wrapper around mdMUReadWrite (setup + the dedupe pipeline).
  - DataContainer                    : holds the input/output file paths and small path helpers.

Where mdMUReadWrite comes from:
  The mdMUReadWrite class lives in mdMatchup_pythoncode.py, a generated Python wrapper over
  mdMatchup.dll and mdGlobalParse.dll that the accompanying
  MelissaMatchupObjectGlobalWindowsPython3.ps1 script downloads on every run.

Reference:
  Quickstart    : https://docs.melissa.com/on-premise-api/matchup-object/matchup-object-quickstart.html
  Release notes : https://releasenotes.melissa.com/on-premise-api/matchup-object/
  Result codes  : https://docs.melissa.com/on-premise-api/matchup-object-global/result-codes.html
"""

import mdMatchup_pythoncode
import os
import sys
import re


class DataContainer:
    """
    Holds the input/output file paths for one pass, plus small path helpers
    (format_output_files derives the output names; get_wrapped wraps a long path for display).
    """
    def __init__(self, input_file_path_1="",  input_file_path_2="", output_file_path_1="", output_file_path_2="", result_codes=[]):

        # Input: path to the global input file.
        self.input_file_path_1 = input_file_path_1

        # Input: path to the US input file.
        self.input_file_path_2 = input_file_path_2

        # Output: derived path for the global results.
        self.output_file_path_1 = output_file_path_1

        # Output: derived path for the US results.
        self.output_file_path_2 = output_file_path_2

        # Result codes are written per record into the output files rather than collected
        # here, so this sample never sets this field.
        self.result_codes = result_codes

    def format_output_files(self):
        """
        Derive each output file path from its input path by inserting "_output" before the
        ".txt" extension (e.g. foo.txt -> foo_output.txt).
        """
        location_1 = self.input_file_path_1.find(".txt")
        location_2 = self.input_file_path_2.find(".txt")
        self.output_file_path_1 = self.input_file_path_1[:location_1] + "_output.txt"
        self.output_file_path_2 = self.input_file_path_2[:location_2] + "_output.txt"

    def get_wrapped(self, path, max_line_length):
        """
        Split a long file path into chunks no longer than max_line_length so it prints
        neatly across several lines in the console output. Display-only helper.
        """
        file = f"{os.getcwd()}\{path}"
        file_parts = file.split(os.sep)
        
        current_line = ""
        wrapped_strings = []

        for section in file_parts:
            if len(current_line + section) > max_line_length:
                wrapped_strings.append(current_line.strip())
                current_line = ""

            if section == file:
                current_line += section
            else:
                current_line += section + os.sep

        if len(current_line) > 0:
            wrapped_strings.append(current_line.strip())

        return wrapped_strings


class MatchUpObjectGlobal:
    """
    Wrapper that owns a single Melissa MatchUp Object Global instance (an mdMUReadWrite) and
    encapsulates one-time setup (license + data files + matchcode) and the per-file dedupe
    pipeline. Reuse one instance across many files; do NOT re-initialize per file.
    """
    def __init__(self, license, data_path):
        """
        Perform the mandatory one-time setup, in this required order:
          1. SetLicenseString        - authorize the object.
          2. SetPathToMatchUpFiles   - tell it where the data files live.
          3. SetKeyFile / SetMatchcodeName / SetMaximumCharacterSize - configure the run.
          4. InitializeDataFiles     - load the data into memory.

        Args:
            license: The Melissa license string used to authorize the object.
            data_path: Path to the folder containing the MatchUp Object Global data files.
        """
        # Path to the MatchUp Object data files.
        self.data_path = data_path

        # Set license string and set path to data files
        # The underlying Melissa MatchUp Object Global instance.
        self.md_matchup_obj = mdMatchup_pythoncode.mdMUReadWrite()
        self.md_matchup_obj.SetLicenseString(license)
        self.md_matchup_obj.SetPathToMatchUpFiles(data_path)
        self.md_matchup_obj.SetKeyFile("temp.key")
        self.md_matchup_obj.SetMatchcodeName("Global Address")
        self.md_matchup_obj.SetMaximumCharacterSize(1)

        # Load the data files. The returned ProgramStatus reports whether initialization succeeded.
        # If you see a different date than expected, check your license string and either download the new data files
        # or use the Melissa Updater program to update your data files.
        p_status = self.md_matchup_obj.InitializeDataFiles()

        # If an issue occurred, please investigate the common causes.
        # Common causes: an invalid/expired license, or missing/wrong-path data files.
        if (p_status != mdMatchup_pythoncode.ProgramStatus.ErrorNone):
            print("Failed to Initialize Object.")
            print(p_status)
            return

        # Diagnostic information, handy for confirming the object loaded the data you expect:

        # Build date of the data files
        print(f"                DataBase Date: {self.md_matchup_obj.GetDatabaseDate()}")

        # When the license stops working
        print(f"              Expiration Date: {self.md_matchup_obj.GetLicenseExpirationDate()}")

        # This number should match with the file properties of the Melissa Object binary file.
        # If TEST appears with the build number, there may be a license key issue.
        print(f"               Object Version: {self.md_matchup_obj.GetBuildNumber()}\n")


    def execute_object_and_result_codes(self, input_file_path, output_file_path):
        """
        Run the MatchUp dedupe pipeline over one input file and write results to an
        output file. Per file: map the matchcode fields, then for each input record
        ClearFields -> AddField -> SetUserInfo -> BuildKey -> WriteRecord; call Process()
        to dedupe; then ReadRecord() each result and write its codes / dupe group / key.

        Args:
            input_file_path: Pipe-delimited input file to read.
            output_file_path: File to write the per-record results to.
        """
        total = 0
        dupes = 0

        # Establish field mappings: when you change the matchcode, you will change these
        self.md_matchup_obj.ClearMappings()

        if (
            self.md_matchup_obj.AddMapping(mdMatchup_pythoncode.MatchcodeMapping.Country) == 0
            or self.md_matchup_obj.AddMapping(mdMatchup_pythoncode.MatchcodeMapping.Address) == 0
            or self.md_matchup_obj.AddMapping(mdMatchup_pythoncode.MatchcodeMapping.Address) == 0
            or self.md_matchup_obj.AddMapping(mdMatchup_pythoncode.MatchcodeMapping.Address) == 0
            or self.md_matchup_obj.AddMapping(mdMatchup_pythoncode.MatchcodeMapping.Address) == 0
        ):
            print("\nError: Incorrect AddMapping() parameter")
            sys.exit(1)

        # Process the sample data file
        try:
            with open(input_file_path, 'r', encoding='utf-8') as in_file, open(output_file_path, 'w', encoding='utf-8') as out_file:

                # Skip the header row
                record = in_file.readline()
                while (record := in_file.readline().strip()):
                    # Read and parse '|' delimited record
                    fields = record.split('|')

                    # Load up the fields
                    self.md_matchup_obj.ClearFields()
                    self.md_matchup_obj.AddField(fields[7])
                    self.md_matchup_obj.AddField(fields[3])
                    self.md_matchup_obj.AddField(fields[4])
                    self.md_matchup_obj.AddField(fields[5])
                    self.md_matchup_obj.AddField(fields[6])

                    # Create a UserInfo string which uniquely identifies the records
                    self.md_matchup_obj.SetUserInfo(fields[0])

                    # Build the key and submit it
                    self.md_matchup_obj.BuildKey()
                    self.md_matchup_obj.WriteRecord()

                # All records are loaded; Process() runs the match/dedupe pass across them.
                self.md_matchup_obj.Process()

                # Write a header row, then read each processed record back and record its result
                # codes, dupe group, and key. "MS03" in the results flags the record as a duplicate.
                header = "Id|ResultCodes|DupeGroup|Key"
                out_file.write(header + '\n')

                # ResultsCodes explain any issues MatchUp Object Global has with the object.
                # List of result codes for MatchUp Object Global
                # https://docs.melissa.com/on-premise-api/matchup-object-global/result-codes.html
                while self.md_matchup_obj.ReadRecord() != 0:
                    if "MS03" in self.md_matchup_obj.GetResults():
                        dupes += 1

                    self.md_matchup_obj.ClearFields()

                    # Prepare and write the output line to the output file
                    arr = [
                        self.md_matchup_obj.GetUserInfo(),
                        self.md_matchup_obj.GetResults(),
                        str(self.md_matchup_obj.GetDupeGroup()),
                        re.sub(r'\s+', ' ', self.md_matchup_obj.GetKey())
                    ]
                    line = '|'.join(arr)
                    out_file.write(line + '\n')

                    total += 1

        except Exception as ex:
            print(ex)


def parse_arguments():
    """
    Read the supported command-line options and return them as a (license, test_us_file,
    test_global_file, data_path) tuple.

    Recognized flags (each followed by its value):
      --license / -l   : the Melissa license string
      --global / -g    : path to the global input file to test in one-shot mode
      --us / -u        : path to the US input file to test in one-shot mode
      --dataPath / -d  : path to the MatchUp Object data files

    Returns:
        A (license, test_us_file, test_global_file, data_path) tuple, each entry
        empty when its flag was not supplied.
    """
    license, test_us_file, test_global_file, data_path = "", "", "", ""

    args = sys.argv
    index = 0
    for arg in args:
        
        if (arg == "--license") or (arg == "-l"):
            if (args[index+1] != None):
                license = args[index+1]
        if (arg == "--global") or (arg == "-g"):
            if (args[index+1] != None):
                test_global_file = args[index+1]
        if (arg == "--us") or (arg == "-u"):
            if (args[index+1] != None):
                test_us_file = args[index+1]
        if (arg == "--dataPath") or (arg == "-d"):
            if (args[index+1] != None):
                data_path = args[index+1]
        index += 1

    return (license, test_us_file, test_global_file, data_path)

def run_as_console(license, test_us_file, test_global_file, data_path):
    """
    Set up the MatchUp Object once, then drive the input -> process -> output cycle.

    In interactive mode (no file args) it loops, asking for the two input files each pass
    until the user answers "N". In one-shot mode (file args supplied) it runs a single
    pass and exits. Each input file is deduped to a matching "_output.txt" file.

    Args:
        license: The Melissa license string used to initialize the object.
        test_us_file: A US input file to process in one-shot mode; if empty, the program
            prompts interactively.
        test_global_file: A global input file to process in one-shot mode.
        data_path: Path to the MatchUp Object data files.
    """
    print("\n\n============= WELCOME TO MELISSA MATCHUP OBJECT GLOBAL WINDOWS PYTHON3 ===============\n")

    # Construct the wrapper. This is where the object is licensed, pointed at the data
    # files, configured, and initialized (see the MatchUpObjectGlobal constructor above).
    matchup_object = MatchUpObjectGlobal(license, data_path)

    should_continue_running = True

    # Gate the program on a successful initialization. If the data files could not be
    # loaded (bad/expired license, missing or wrong-path data files, ...),
    # GetInitializeErrorString() returns the reason instead of "No Error" and we skip
    # the processing loop entirely.
    if matchup_object.md_matchup_obj.GetInitializeErrorString() != "No Error":
      should_continue_running = False

    while should_continue_running:
        if (test_us_file == None or test_us_file == "") or (test_global_file == None or test_global_file == ""):
          # Interactive mode: prompt the user for the two input file paths.
          print("\nFill in each value to see the MatchUp Object Global results")
          input_file_path_1 = str(input("Global Input File: "))
          input_file_path_2 = str(input("US Input File: "))
        else:
          # One-shot mode: use the file paths passed on the command line.
          input_file_path_1 = test_us_file
          input_file_path_2 = test_global_file

        # Holder for this pass's input/output file paths.
        data_container = DataContainer(input_file_path_1, input_file_path_2)

        # Print user input
        print("\n======================================= INPUTS =======================================\n")
        sections = data_container.get_wrapped(data_container.input_file_path_1, 50)

        print(f"\t        Global Input File: {sections[0]}")

        for i in range(1, len(sections)):
            if i == len(sections) - 1 and sections[i].endswith("/"):
                sections[i] = sections[i][:-1]
            print(f"\t                           {sections[i]}")

        sections = data_container.get_wrapped(data_container.input_file_path_2, 50)

        print(f"\t            US Input File: {sections[0]}")

        for i in range(1, len(sections)):
            if i == len(sections) - 1 and sections[i].endswith("/"):
                sections[i] = sections[i][:-1]
            print(f"\t                           {sections[i]}")

        # Derive each output path from its input path (e.g. foo.txt -> foo_output.txt).
        data_container.format_output_files()

        # Execute MatchUp Object Global
        # Dedupe each input file independently, writing results to its output file.
        matchup_object.execute_object_and_result_codes(input_file_path_1, data_container.output_file_path_1)
        matchup_object.execute_object_and_result_codes(input_file_path_2, data_container.output_file_path_2)

        # Print output
        print("\n======================================= OUTPUT =======================================\n")

        
        sections1 = data_container.get_wrapped(data_container.input_file_path_1, 50)

        print("\n  MatchUp Object Global Information:")
        print(f"\t       Global Output File: {sections1[0]}")

        for i in range(1, len(sections1)):
            if i == len(sections1) - 1 and sections1[i].endswith("/"):
                sections1[i] = sections1[i][:-1]
            print(f"\t                           {sections1[i]}")

        sections2 = data_container.get_wrapped(data_container.input_file_path_2, 50)

        print(f"\t           US Output File: {sections2[0]}")

        for i in range(1, len(sections2)):
            if i == len(sections2) - 1 and sections2[i].endswith("/"):
                sections2[i] = sections2[i][:-1]
            print(f"\t                           {sections2[i]}")




        is_valid = False

        # In one-shot mode there is nothing more to do after a single pass: mark the
        # input handled and stop the outer loop.
        if not ((test_us_file == None or test_us_file == "") and (test_global_file == None or test_global_file == "")):
            is_valid = True
            should_continue_running = False
        # Interactive mode: ask whether to process another pair of files. Keep prompting
        # until we get a valid Y/N. "N" ends the program; "Y" falls through to another pass.
        while not is_valid:

            test_another_response = input(str("\nTest another file? (Y/N)\n"))


            if not (test_another_response == None or test_another_response == ""):
                test_another_response = test_another_response.lower()
            if test_another_response == "y":
                is_valid = True

            elif test_another_response == "n":
                is_valid = True
                should_continue_running = False
            else:

              print("Invalid Response, please respond 'Y' or 'N'")

    print("\n======================= THANK YOU FOR USING MELISSA PYTHON OBJECT ====================\n")


# ---------------------------- MAIN STARTS HERE ----------------------------

# Read the optional command-line arguments, then hand control to run_as_console, which
# performs the actual MatchUp Object Global setup and processing.
license, test_us_file, test_global_file, data_path = parse_arguments()

run_as_console(license, test_us_file, test_global_file, data_path)