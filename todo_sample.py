""" sample program demoing todo.py """

# from tools.todo import Todo
from tools.todo import TodoConfig
from tools.todo import TodoList
from tools.todo import Todo
import tools.file_module as fm
import os

todo_list = ["x  2020-12-02 2020-12-01 Python with Deskbike @Computer +Python @Deskbike +Health",
             "x  2020-12-02 2020-12-01 Python with Deskbike +Python +Health @Computer @Deskbike",
             "x 2020-12-20 Visit Stuttgart +Friend @Offsite due:2020-12-12 other_attribute:34",
             "(A) 2020-8-20 NO ATTRIBUTES due:2020-12-12",
             "2020-11-20 Yet another task + @Offsite due:2020-12-12",
             "(C) Visit Another +Friend @Offsite due:2020-12-12 hash:b06e78f00e8689ec52da48aaae4d6553",
             "(C) Visit Another HASH +Friend @Offsite hash:45rerererer due:2020-12-12"
             ]

# transform from string list to dict
# todo_dict = Todo.get_dict_from_todo(todo_list, show_info=False)
# transform back from dict to string
# todo_list = Todo.get_todo_from_dict(todo_dict, show_info=False,calc_hash=False)
# print("\n".join(todo_list))

# sample_task="x (B) 2023-05-23 2023-05-23 Sample Task +Project @Context1 @Context2 att1:value1 att2:value2 url:http://www.abc.com hash:12345abcdef"

f=r"xxxx"
# config=fm.read_yaml(f)

todo_list = TodoList(f)
todo_list.read_list(read_archive=True)
#todo=todo_list.get_todo(4,as_string=False)
todo_dict=todo_list.get_todo(2,as_dict=True)
# todo_list.backup()

# print(todo)
print("END")
