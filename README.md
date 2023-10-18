# Melissa - MatchUp Object Global Windows Python3

## Purpose

This code showcases the Melissa MatchUp Object Global using Python3.

Please feel free to copy or embed this code to your own project. Happy coding!

For the latest Melissa MatchUp Object Global release notes, please visit: https://releasenotes.melissa.com/on-premise-api/matchup-object-global/

For further details, please visit: https://wiki.melissadata.com/index.php?title=MatchUp_Object:Reference

The console will ask the user for:

- A txt file that contains global data you would like to matchup
- A txt file that contains US data you would like to matchup

And return 

- A txt file of global duplicate groups
- A txt file of US duplicate groups

## Tested Environments

- Windows 64-bit Python 3.8.7
- Powershell 5.1
- Melissa data files for 2023-Q3

## Required File(s) and Programs

#### Binaries
This is the c++ code of the Melissa Object.

- mdMatchup.dll
- mdGlobalParse.dll

#### Data File(s)
- icudt52l.dat
- mdMatchup.dat
- mdMatchup.mc
- mdMatchup.sac
- mdMatchup.cfg


## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

This project is compatible with Python3

#### Install Python3
Before starting, make sure that Python3 has been correctly installed on your machine and your environment paths are configured. 

You can download Python here: 
https://www.python.org/downloads/

To set up your Path to correctly to use the python3 command, execute the following steps:
1) Run Powershell as an administrator 
2) Execute the command: 
`New-Item -ItemType SymbolicLink -Path "Link" -Target "Target"`

    where "Target" is the path to py.exe (by default this should be "C:\Windows\py.exe")\
    and "Link" is the path to py.exe, but "py.exe" is replaced with "python3.exe"\
    For Example:\
    `New-Item -ItemType SymbolicLink -Path "C:\Windows\python3.exe" -Target "C:\Windows\py.exe"`

If you are unsure, you can check by opening a command prompt window and typing the following:
`python3 --version`

![alt text](/screenshots/python_version.PNG)

If you see the version number then you have installed Python3 and set up your environment paths correctly!

----------------------------------------

#### Set up Powershell settings

If running Powershell for the first time, you will need to run this command in the Powershell console: `Set-ExecutionPolicy RemoteSigned`.
The console will then prompt you with the following warning shown in the image below. 
 - Enter `'A'`. 
 	- If successful, the console will not output any messages. (You may need to run Powershell as administrator to enforce this setting).
	
 ![alt text](/screenshots/powershell_executionpolicy.png)

----------------------------------------

#### Download this project
```
$ git clone https://github.com/MelissaData/MatchUpObjectGlobal-Python3
$ cd MatchUpObjectGlobal-Python3
```

#### Set up Melissa Updater 

Melissa Updater is a CLI application allowing the user to update their Melissa applications/data. 

- Download Melissa Updater here: <https://releases.melissadata.net/Download/Library/WINDOWS/NET/ANY/latest/MelissaUpdater.exe>
- Create a folder within the cloned repo called `MelissaUpdater`.
- Put `MelissaUpdater.exe` in `MelissaUpdater` folder you just created.

----------------------------------------

#### Different ways to get data file(s)
1.  Using Melissa Updater
	- It will handle all of the data download/path and dll(s) for you. 
2.  If you already have the latest zip, you can find the data file(s) and dll(s) in there
	- Use the location of where you copied/installed the data and update the "$DataPath" variable in the powershell script.
	- Copy all the dll(s) mentioned above into the `MelissaMatchUpObjectGlobalWindowsPython3` project folder.
	
----------------------------------------

## Run Powershell Script
Parameters:
- -global: a test global txt file
- -us: a test US txt file

  These are convenient when you want to get results for specific txt files in one run instead of testing multiple txt files in interactive mode.

- -license (optional): a license string to test the MatchUp Object Global
- -quiet (optional): add to the command if you do not want to get any console output from the Melissa Updater


When you have modified the script to match your data location, let's run the script. There are two modes:
- Interactive 

	The script will prompt the user for a txt file, then use the provided txt file to test MatchUp Object Global.  For example:
    ```
    $ .\MelissaMatchupObjectGlobalWindowsPython3.ps1
    ```
    For quiet mode:
    ```
    $ .\MelissaMatchupObjectGlobalWindowsPython3.ps1 -quiet
    ```
- Command Line 

    You can pass a global txt file, us txt file, and a license string into the ```-global```, ```-us```, and ```-license``` parameters respectively to test MatchUp Object Global. For example:
    ```
    $ .\MelissaMatchupObjectGlobalWindowsPython3.ps1 -global "MelissaMatchupGlobalSampleInput.txt" -us "MelissaMatchupUSSampleInput.txt"
    $ .\MelissaMatchupObjectGlobalWindowsPython3.ps1 -global "MelissaMatchupGlobalSampleInput.txt" -us "MelissaMatchupUSSampleInput.txt" -license "<your_license_string>"
    ```
    For quiet mode:
    ```
    $ .\MelissaMatchupObjectGlobalWindowsPython3.ps1 -global "MelissaMatchupGlobalSampleInput.txt" -us "MelissaMatchupUSSampleInput.txt" -quiet
    $ .\MelissaMatchupObjectGlobalWindowsPython3.ps1 -global "MelissaMatchupGlobalSampleInput.txt" -us "MelissaMatchupUSSampleInput.txt" -license "<your_license_string>" -quiet
    ```
This is the expected output from a successful setup for interactive mode:


![alt text](/screenshots/output.png)


## Contact Us

For free technical support, please call us at 800-MELISSA ext. 4
(800-635-4772 ext. 4) or email us at tech@melissa.com.

To purchase this product, contact Melissa sales department at
800-MELISSA ext. 3 (800-635-4772 ext. 3).
