# TOC
* [CONFIGURATION PATTERN](#configuration-pattern)
  * [PATTERN notepadpp](#pattern-notepadpp)
  * [PATTERN vscode](#pattern-vscode)
  * [PATTERN vscode_diff](#pattern-vscode_diff)
* [CONFIGURATION EXECUTABLE](#configuration-executable)
  * [EXECUTABLE notepadpp](#executable-notepadpp)
  * [EXECUTABLE vscode](#executable-vscode)
  * [EXECUTABLE cygwin](#executable-cygwin)
* [CONFIGURATION FILE](#configuration-file)
  * [FILE todo_file](#file-todo_file)
  * [FILE cc_config_file](#file-cc_config_file)
  * [FILE cc_report_file](#file-cc_report_file)
  * [FILE absolute_file_path](#file-absolute_file_path)
  * [FILE file_name_and_path](#file-file_name_and_path)
  * [FILE file_name_and_ext_path](#file-file_name_and_ext_path)
  * [FILE file_name_ext_path_only](#file-file_name_ext_path_only)
  * [FILE xyz](#file-xyz)
* [CONFIGURATION PATH](#configuration-path)
  * [PATH cwd](#path-cwd)
  * [PATH cc_home](#path-cc_home)
  * [PATH folder_in_environment](#path-folder_in_environment)
  * [PATH work_folder](#path-work_folder)
  * [PATH favorites_folder](#path-favorites_folder)
  * [PATH wrong_folder](#path-wrong_folder)
* [CONFIGURATION SCRIPT](#configuration-script)
* [CONFIGURATION SCRIPT_BASH](#configuration-script_bash)
  * [SCRIPT_BASH bat1](#script_bash-bat1)
* [CONFIGURATION ENVIRONMENT_WIN](#configuration-environment_win)
  * [ENVIRONMENT_WIN folder_in_environment](#environment_win-folder_in_environment)
  * [ENVIRONMENT_WIN howto](#environment_win-howto)
  * [ENVIRONMENT_WIN valid_path](#environment_win-valid_path)
  * [ENVIRONMENT_WIN valid_file](#environment_win-valid_file)
  * [ENVIRONMENT_WIN howto2](#environment_win-howto2)
* [CONFIGURATION ENVIRONMENT_BASH](#configuration-environment_bash)
  * [ENVIRONMENT_BASH howto](#environment_bash-howto)
  * [ENVIRONMENT_BASH howto2](#environment_bash-howto2)
* [CONFIGURATION SHORTCUT](#configuration-shortcut)
  * [SHORTCUT cc_report](#shortcut-cc_report)
  * [SHORTCUT cygwin](#shortcut-cygwin)
  * [SHORTCUT bat1](#shortcut-bat1)
  * [SHORTCUT my_doc](#shortcut-my_doc)
* [CONFIGURATION CMD_PARAM](#configuration-cmd_param)
  * [CMD_PARAM cmdparam_notepadpp](#cmd_param-cmdparam_notepadpp)
  * [CMD_PARAM cmdparam_vscode](#cmd_param-cmdparam_vscode)
  * [CMD_PARAM cmdparam_default](#cmd_param-cmdparam_default)
  * [CMD_PARAM cmd_client_main](#cmd_param-cmd_client_main)
  * [CMD_PARAM cmdparam_template](#cmd_param-cmdparam_template)
* [CONFIGURATION CMD_SUBPARSER](#configuration-cmd_subparser)
  * [CMD_SUBPARSER subparser_sample_config](#cmd_subparser-subparser_sample_config)
  * [CMD_SUBPARSER subparser_cmd_client](#cmd_subparser-subparser_cmd_client)
* [CONFIGURATION CMD_MAP](#configuration-cmd_map)
  * [CMD_MAP cmdparam_notepadpp](#cmd_map-cmdparam_notepadpp)
  * [CMD_MAP cmdparam_vscode](#cmd_map-cmdparam_vscode)
  * [CMD_MAP cmd_client_main](#cmd_map-cmd_client_main)
* [CONFIGURATION CMD_INPUT_MAP](#configuration-cmd_input_map)
  * [CMD_INPUT_MAP default](#cmd_input_map-default)
  * [CMD_INPUT_MAP main](#cmd_input_map-main)
  * [CMD_INPUT_MAP npp](#cmd_input_map-npp)
# CONFIGURATION PATTERN
## PATTERN `notepadpp`
```
{[notepadpp]} {[file]} {-n[line]} {[extra]}
```
**DESCRIPTION**: Opens Notepad++: [notepadpp] -n[line] [extra]
* **`notepadpp`**  [`executable`] (Path to notepad++.exe)  
  * `resolved`:``` C:\<PATH_TO>\notepad++.exe```
* **`file`**  [`file`] (File to be opened)  
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`line`**  [`param`] (File to be opened at line number)  
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`extra`**  [`param`] (Additional params (in quotes) to be appended to command)  
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
## PATTERN `vscode`
```
{[vscode]} --goto "{[file]}{:[line]}" {[extra]}
```
**DESCRIPTION**: Opens VSCODE: [vscode] [file] at [line] with [extra]
* **`vscode`**  [`executable`] (Path to code.exe)  
  * `resolved`:``` C:\<PATH_TO>\Code.exe```
* **`file`**  [`file`] (File to be opened)  
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`line`**  [`param`] (File to be opened at line number)  
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`extra`**  [`param`] (Additional params (in quotes) to be appended to command)  
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
## PATTERN `vscode_diff`
```
{[vscode]} --diff {[oldfile]} {[newfile]}
```
**DESCRIPTION**: Performs diff in Visual Codes: [vscode] [oldfile] [newfile]
* **`vscode`**  [`executable`] (Executable Path)  
  * `resolved`:``` C:\<PATH_TO>\Code.exe```
* **`a_file`** [`refers to:absolute_file_path`]:  [`file`]  
  * `resolved`:``` C:\<PATH_TO>\test.png```
* **`just_param`**  [`param`]  
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`a_ref_path`** [`refers to:howto`]:  [`path`]  
  * `path: environment_win`
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`a_file_path`** [`refers to:howto`]:  [`path`]  
  * `path: environment_win`
  * `resolved`:``` [NO_RESOLVED_REF]```
* **`newfile`** [`refers to:folder_in_environment`]:  [`file`]  
  * `path: path`
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
# CONFIGURATION EXECUTABLE
## EXECUTABLE `notepadpp`
**DESCRIPTION**: Path to Notepad++
* **`notepadpp`**  (Path to Notepad++)  
  * `file: notepad++.exe`
  * `path: C:/<PATHTO>/Notepad++`
  * `resolved`:``` C:\<PATH_TO>\notepad++.exe```

  _[TOC](#toc)_
## EXECUTABLE `vscode`
**DESCRIPTION**: Path to VS Code
* **`vscode`**  (Path to VS Code)  
  * `file: Code.exe`
  * `path: C:/<path_to>/VSCode`
  * `resolved`:``` C:\<PATH_TO>\Code.exe```

  _[TOC](#toc)_
## EXECUTABLE `cygwin`
**DESCRIPTION**: short help text goes here
* **`cygwin`**  (short help text goes here)  
  * `file: xyz`
  * `resolved`:``` C:\<PATH_TO>\cmd_client\param_config.yaml```

  _[TOC](#toc)_
# CONFIGURATION FILE
## FILE `todo_file`
**DESCRIPTION**: TODO.TXT File
* **`todo_file`**  (TODO.TXT File)  
  * `file: todo.txt`
  * `path: C:/<PATH_TO>/CMD/todo/todo_txt`
  * `resolved`:``` C:\<PATH_TO>\Henrik\LaufendeDokumente\CMD\todo\todo_txt\todo.txt```

  _[TOC](#toc)_
## FILE `cc_config_file`
**DESCRIPTION**: CONFIG File for the Command Center
* **`cc_config_file`**  (CONFIG File for the Command Center)  
  * `file: param_config.yaml`
  * `path: cc_home`
  * `resolved`:``` C:\<PATH_TO>\cmd_client\param_config.yaml```

  _[TOC](#toc)_
## FILE `cc_report_file`
**DESCRIPTION**: File to be created for the Command Center
* **`cc_report_file`**  (File to be created for the Command Center)  
  * `file: cc_report.md`
  * `path: cwd`
  * `resolved`:``` C:\<PATH_TO>\cc_report.md```

  _[TOC](#toc)_
## FILE `absolute_file_path`
**DESCRIPTION**: sample for an absolute file
* **`absolute_file_path`**  (sample for an absolute file)  
  * `file: C:/<PATH_TO>/test.png`
  * `resolved`:``` C:\<PATH_TO>\test.png```

  _[TOC](#toc)_
## FILE `file_name_and_path`
**DESCRIPTION**: sample for an absolute fiöe
* **`file_name_and_path`**  (sample for an absolute fiöe)  
  * `file: test.png`
  * `path: C:/<PATH_TO>`
  * `resolved`:``` C:\<PATH_TO>\test.png```

  _[TOC](#toc)_
## FILE `file_name_and_ext_path`
**DESCRIPTION**: sample for an absolute fiöe
* **`file_name_and_ext_path`** [`refers to:valid_path`]:  (sample for an absolute fiöe)  
  * `file: test.png`
  * `path: environment_win`
  * `resolved`:``` C:\<PATH_TO>\test.png```

  _[TOC](#toc)_
## FILE `file_name_ext_path_only`
**DESCRIPTION**: sample for an absolute fiöe
* **`file_name_ext_path_only`** [`refers to:valid_file`]:  (sample for an absolute fiöe)  
  * `file: environment_win`
  * `path: environment_win`
  * `resolved`:``` C:\<PATH_TO>\test.png```

  _[TOC](#toc)_
## FILE `xyz`
**DESCRIPTION**: sample for a referenced file
* **`xyz`**  (sample for a referenced file)  
  * `file: C:/<path_to>/root/tools/cmd_client/param_config.yaml`
  * `resolved`:``` C:\<PATH_TO>\cmd_client\param_config.yaml```

  _[TOC](#toc)_
# CONFIGURATION PATH
## PATH `cwd`
**DESCRIPTION**: Current Working Directory
* **`cwd`**  (Current Working Directory)  
  * `path: .`
  * `resolved`:``` C:\<PATH_TO>```

  _[TOC](#toc)_
## PATH `cc_home`
**DESCRIPTION**: Command Center HOME Directory
* **`cc_home`**  (Command Center HOME Directory)  
  * `path: C:/<path_to>/root/tools/cmd_client`
  * `resolved`:``` C:\<PATH_TO>\cmd_client```

  _[TOC](#toc)_
## PATH `folder_in_environment`
**DESCRIPTION**: xdrf
* **`folder_in_environment`** [`refers to:howto`]:  (xdrf)  
  * `path: environment_win`
  * `resolved`:``` C:\```

  _[TOC](#toc)_
## PATH `work_folder`
**DESCRIPTION**: xdrf
* **`work_folder`**  (xdrf)  
  * `path: path>work_folder`
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
## PATH `favorites_folder`
**DESCRIPTION**: xdrf
* **`favorites_folder`**  (xdrf)  
  * `path: C:/<PATH_TO>`
  * `resolved`:``` C:\<PATH_TO>```

  _[TOC](#toc)_
## PATH `wrong_folder`
**DESCRIPTION**: xdrf
* **`wrong_folder`**  (xdrf)  
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
# CONFIGURATION SCRIPT
# CONFIGURATION SCRIPT_BASH
## SCRIPT_BASH `bat1`
**DESCRIPTION**: short help text goes here
* **`bat1`**  (short help text goes here)  
  * `file: xyz`
  * `resolved`:``` C:\<PATH_TO>\cmd_client\param_config.yaml```

  _[TOC](#toc)_
# CONFIGURATION ENVIRONMENT_WIN
## ENVIRONMENT_WIN `folder_in_environment`
**DESCRIPTION**: description
* **`folder_in_environment`**  (description)  
  * `path: C:/<path_to>`
  * `value: xyz`
  * `resolved`:``` C:\<path_to>```

  _[TOC](#toc)_
## ENVIRONMENT_WIN `howto`
**DESCRIPTION**: description
* **`howto`**  (description)  
  * `path: C:/`
  * `value: xyz`
  * `resolved`:``` C:\```
  * `export to env: C:\`

  _[TOC](#toc)_
## ENVIRONMENT_WIN `valid_path`
**DESCRIPTION**: description
* **`valid_path`**  (description)  
  * `path: C:/<PATH_TO>`
  * `value: xyz`
  * `resolved`:``` C:\<PATH_TO>```
  * `export to env: xyz`

  _[TOC](#toc)_
## ENVIRONMENT_WIN `valid_file`
**DESCRIPTION**: description
* **`valid_file`**  (description)  
  * `file: C:/<PATH_TO>/test.png`
  * `value: xyz`
  * `resolved`:``` C:\<PATH_TO>\test.png```

  _[TOC](#toc)_
## ENVIRONMENT_WIN `howto2`
**DESCRIPTION**: description
* **`howto2`**  (description)  
  * `file: xyz`
  * `path: optional`
  * `value: xyz`
  * `resolved`:``` C:\<PATH_TO>\cmd_client\param_config.yaml```

  _[TOC](#toc)_
# CONFIGURATION ENVIRONMENT_BASH
## ENVIRONMENT_BASH `howto`
**DESCRIPTION**: description
* **`howto`**  (description)  
  * `path: optional`
  * `value: xyz`
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
## ENVIRONMENT_BASH `howto2`
**DESCRIPTION**: description
* **`howto2`**  (description)  
  * `file: xyz`
  * `path: optional`
  * `value: xyz`
  * `resolved`:``` C:\<PATH_TO>\cmd_client\param_config.yaml```

  _[TOC](#toc)_
# CONFIGURATION SHORTCUT
## SHORTCUT `cc_report`
**DESCRIPTION**: ACTION: Creates the Configuration Report (Markdown Format)
* **`cc_report`**  (ACTION: Creates the Configuration Report (Markdown Format))  
  * `file: cc_report_file`
  * `resolved`:``` C:\<PATH_TO>\cc_report.md```

  _[TOC](#toc)_
## SHORTCUT `cygwin`
**DESCRIPTION**: Display Path: -d -a [<filename>]/-p <.|path>
* **`cygwin`**  (Display Path: -d -a [<filename>]/-p <.|path>)  
  * `file: cygwin.exe`
  * `path: sdsd`
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
## SHORTCUT `bat1`
**DESCRIPTION**: Display Path: -d -a [<filename>]/-p <.|path>
* **`bat1`**  (Display Path: -d -a [<filename>]/-p <.|path>)  
  * `file: bat1`
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
## SHORTCUT `my_doc`
**DESCRIPTION**: this is my knowledge collection
* **`my_doc`**  (this is my knowledge collection)  
  * `file: howto`
  * `resolved`:``` [NO_RESOLVED_REF]```

  _[TOC](#toc)_
# CONFIGURATION CMD_PARAM
## CMD_PARAM `cmdparam_notepadpp`
**DESCRIPTION**: Notepad++ Command Line Input
* **`file`**: File to be opened  
```
   [-f/--file] [file] 
```  
* **`line`**: Open File at submitted Line  
```
   [-l/--line] [line] 
```  
* **`extra`**: Extra parameters, will be appended to command  
```
   [-x/--extra] [..extra params..] 
```  
* **`todo`**: Opens todo.txt file  
```
   [-ot/--todo]  
```  

  _[TOC](#toc)_
## CMD_PARAM `cmdparam_vscode`
**DESCRIPTION**: VSCODE Command Line Input
* **`file`**: File to be opened  
```
   [-f/--file] [file] 
```  
* **`line`**: Open File at submitted Line  
```
   [-l/--line] [line] 
```  
* **`extra`**: Extra parameters, will be appended to command  
```
   [-x/--extra] [..extra params..] 
```  

  _[TOC](#toc)_
## CMD_PARAM `cmdparam_default`
**DESCRIPTION**: often used default parameters
* **`file`**: Input File  
```
   [-f/--file] [file] 
```  
* **`file_out`**: Output File  
```
   [-fo/--file_out] [file_out] 
```  
* **`csv_separator`**: CSV separator, default is ';'  
```
   [-csep/--csv_sep] [;] (DEFAULT: ;)
```  
* **`decimal_separator`**: decimal spearator, default is ','  
```
   [-dsep/--dec_sep] [,] (DEFAULT: ,)
```  
* **`loglevel`**: Set loglevel (debug,info,warning,error)  
```
   [-ll/--loglevel] [loglevel] (DEFAULT: info)
```  
* **`add_timestamp`**: Help Comment True  
```
   [-ts/--add_timestamp]  
```  

  _[TOC](#toc)_
## CMD_PARAM `cmd_client_main`
**DESCRIPTION**: Main parameters for the cmd_client
* **`cc_report`**: Create Command Center Configuration Report  
```
   [-ccr/--cc_report]  
```  
* **`param_short`**: Help Comment  
```
   [-ps/--param_short] [param_short] 
```  

  _[TOC](#toc)_
## CMD_PARAM `cmdparam_template`
**DESCRIPTION**: description of the cmdparams template
* **`sample_param`**: Help Comment  
```
   [-ps/--param_short] [param_short] 
```  
* **`sample_bool_true`**: Help Comment True  
```
   [-sbt/--sbtrue]  
```  
* **`sample_bool_false`**: Help Comment False  
```
   [-sbf/--sbfalse]  
```  

  _[TOC](#toc)_
# CONFIGURATION CMD_SUBPARSER
## CMD_SUBPARSER `subparser_sample_config`
1. **`subparser`**: [cmdparam_template](#cmd_param-cmdparam_template)

  _[TOC](#toc)_
## CMD_SUBPARSER `subparser_cmd_client`
1. **`subparser`**: [cmdparam_notepadpp](#cmd_param-cmdparam_notepadpp)
1. **`subparser`**: [cmdparam_vscode](#cmd_param-cmdparam_vscode)

  _[TOC](#toc)_
# CONFIGURATION CMD_MAP
## CMD_MAP `cmdparam_notepadpp`
**DESCRIPTION**: Map Input Params to Notepad++
  * **MAPPING TYPE**: `pattern`
  * **COMMAND LINE PROFILE** [`cmdparam_notepadpp`](#cmd_param-cmdparam_notepadpp)
  * **PATTERN**: [`notepadpp`](#pattern-notepadpp)

  _[TOC](#toc)_
## CMD_MAP `cmdparam_vscode`
**DESCRIPTION**: Map Input Params to VSCode
  * **MAPPING TYPE**: `pattern`
  * **COMMAND LINE PROFILE** [`cmdparam_vscode`](#cmd_param-cmdparam_vscode)
  * **PATTERN**: [`vscode`](#pattern-vscode)

  _[TOC](#toc)_
## CMD_MAP `cmd_client_main`
**DESCRIPTION**: Map Main Parameters to Commands
* **OPTION** `cc_report` (config type: [`shortcut-cc_report`](#shortcut-cc_report))  
ACTION: Creates the Configuration Report (Markdown Format)
  * `file`: ```cc_report_file```
  * `action`: ```create_report```
  * `resolved_path_ref`: ```C:\<PATH_TO>```
  * `resolved_file_ref`: ```C:\<PATH_TO>\cc_report.md```

  _[TOC](#toc)_
# CONFIGURATION CMD_INPUT_MAP
## CMD_INPUT_MAP `default`
**DESCRIPTION**: Maps the default parser arguments (`cmdparam_default`) to configuration
* **CMD INPUT MAP** `dummy` (Just a dummy map)
  * [Config Path  (resolved)](#file-cc_report_file) ```[type>param>key]: [file>cc_report_file>file] => hugo``` (parser value)
  * [Config Path  (resolved)](#file-test_another_param) ```[type>param>key]: [file>test_another_param>test] => hugo2``` (parser value)

  _[TOC](#toc)_
## CMD_INPUT_MAP `main`
**DESCRIPTION**: Maps the main parser (`cmd_client_main`) to configuration
* **CMD INPUT MAP** `param_short` 
  * [Config Path  (resolved)](#file-cc_report_file) ```[type>param>key]: [file>cc_report_file>file] => hugo``` (parser value)

  _[TOC](#toc)_
## CMD_INPUT_MAP `npp`
**DESCRIPTION**: Maps the Notepad++ subparser (`cmdparam_notepadpp`) to configuration
* **CMD INPUT MAP** `todo` (Testing the map)
  * [Config Path  (resolved)](#path-cc_home) ```[type>param>key]: [path>cc_home>path] => path``` (parser value)

  _[TOC](#toc)_
----
**`Configuration (C:\<PATH_TO>\cmd_client\param_config.yaml) / 2023-11-01 13:46:19`**