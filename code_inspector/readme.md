# Generating Class Diagrams with Plant UML using Inspect

The module `inspect_example.py` will create plant UML component and class diagrams to be generated with [plantuml](https://plantuml.com/en).

As opposed to to [`py2puml`](https://github.com/lucsorel/py2puml), also generation of the non class parts is supported. 

It will instanciate modules that are found in a root path and will try to get all all inner/external dependencies as well as inheritance relations. This works only, if Classes can be instancited using a blank Constructor. The only difference Class vs. Instance are the missing instance variables. 

**Prerequisite**: All modules referenced can be loaded (i.e. virtual env is correctly activated)

**Usage**: Check the code in the `__main__` section of the file. In essence all you need to do is to import all required packages, define a root path and instanciate the model, and create the UML file from there.  

Afterwards you call `plantuml`to generate the image (shown for Windows):

```
cd "C:\<Path to your plantuml file>\"
# here we use filename test.plantuml
java -jar "C:\<path_to\plantuml.jar" test.plantuml
start test.png
```

**Generating the Class Diagram**  
A generated sample [`sample_instance.plantuml`](artifacts/sample_instance.plantuml) diagram file using the classes in this folder (works omly if `model_instance` is `True`):  

![sample uml class diagram](artifacts/sample_instance.png)

If Instanciation of Instances leads to errors, set the parameter `model_instance` to `False` (as shown in `main`). The [`sample.plantuml`](artifacts/sample.plantuml) lists only static class attributes, in the UML diagram instance attributes are omitted:

![sample uml class diagram](artifacts/sample.png)


**NOTES**: Since Python also allows non encapsulated parts, these will be shown as a pseudo class (shown as stereotype `<<moduleclass>>`). Any classes are shown as entities linked to this pseudo class.

**Generating the Component Diagram**  
A generated sample plantuml component diagram file using the classes in this folder: [`sample_component.plantuml`](artifacts/sample_component.plantuml).  
![sample uml component diagram ](artifacts/sample_component.png)  
**NOTE**: This diagram requires the `tree utility` for generation

**Limitations**
* Annotations not supported